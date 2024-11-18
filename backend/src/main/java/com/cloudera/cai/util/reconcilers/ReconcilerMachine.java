/*
 * CLOUDERA APPLIED MACHINE LEARNING PROTOTYPE (AMP)
 * (C) Cloudera, Inc. 2024
 * All rights reserved.
 *
 * Applicable Open Source License: Apache 2.0
 *
 * NOTE: Cloudera open source products are modular software products
 * made up of hundreds of individual components, each of which was
 * individually copyrighted.  Each Cloudera open source product is a
 * collective work under U.S. Copyright Law. Your license to use the
 * collective work is as provided in your written agreement with
 * Cloudera.  Used apart from the collective work, this file is
 * licensed for your use pursuant to the open source license
 * identified above.
 *
 * This code is provided to you pursuant a written agreement with
 * (i) Cloudera, Inc. or (ii) a third-party authorized to distribute
 * this code. If you do not have a written agreement with Cloudera nor
 * with an authorized and properly licensed third party, you do not
 * have any rights to access nor to use this code.
 *
 * Absent a written agreement with Cloudera, Inc. ("Cloudera") to the
 * contrary, A) CLOUDERA PROVIDES THIS CODE TO YOU WITHOUT WARRANTIES OF ANY
 * KIND; (B) CLOUDERA DISCLAIMS ANY AND ALL EXPRESS AND IMPLIED
 * WARRANTIES WITH RESPECT TO THIS CODE, INCLUDING BUT NOT LIMITED TO
 * IMPLIED WARRANTIES OF TITLE, NON-INFRINGEMENT, MERCHANTABILITY AND
 * FITNESS FOR A PARTICULAR PURPOSE; (C) CLOUDERA IS NOT LIABLE TO YOU,
 * AND WILL NOT DEFEND, INDEMNIFY, NOR HOLD YOU HARMLESS FOR ANY CLAIMS
 * ARISING FROM OR RELATED TO THE CODE; AND (D)WITH RESPECT TO YOUR EXERCISE
 * OF ANY RIGHTS GRANTED TO YOU FOR THE CODE, CLOUDERA IS NOT LIABLE FOR ANY
 * DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, PUNITIVE OR
 * CONSEQUENTIAL DAMAGES INCLUDING, BUT NOT LIMITED TO, DAMAGES
 * RELATED TO LOST REVENUE, LOST PROFITS, LOSS OF INCOME, LOSS OF
 * BUSINESS ADVANTAGE OR UNAVAILABILITY, OR LOSS OR CORRUPTION OF
 * DATA.
 */

package com.cloudera.cai.util.reconcilers;

import static com.cloudera.cai.rag.configuration.ObservabilityConfiguration.noopOpenTelemetry;
import static io.opentelemetry.api.common.AttributeKey.longKey;
import static java.util.concurrent.TimeUnit.SECONDS;

import io.opentelemetry.api.OpenTelemetry;
import io.opentelemetry.api.common.AttributeKey;
import io.opentelemetry.api.trace.SpanBuilder;
import io.opentelemetry.api.trace.StatusCode;
import io.opentelemetry.api.trace.Tracer;
import io.opentelemetry.context.Scope;
import java.util.HashSet;
import java.util.LinkedList;
import java.util.Random;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.locks.Condition;
import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReentrantLock;
import java.util.stream.Collectors;
import lombok.extern.slf4j.Slf4j;

@Slf4j
class ReconcilerMachine<T> {
  private static final ExecutorService RECONCILER_EXECUTOR =
      Executors.newVirtualThreadPerTaskExecutor();
  private static final AttributeKey<String> RECONCILER_NAME_ATTRIBUTE_KEY =
      AttributeKey.stringKey("reconciler");
  private static final AttributeKey<Long> NUMBER_OF_ITEMS_ATTRIBUTE_KEY = longKey("numberOfItems");

  private static final Random random = new Random();
  private final HashSet<T> elements = new HashSet<>();
  private final LinkedList<T> order = new LinkedList<>();
  private final Lock lock = new ReentrantLock();
  private final Condition notEmpty = lock.newCondition();
  // To prevent OptimisticLockException
  private final Set<T> processingIdSet = ConcurrentHashMap.newKeySet();
  private final boolean deduplicate;
  private final ReconcilerConfig config;
  private final Tracer tracer;

  ReconcilerMachine(ReconcilerConfig config, boolean deduplicate, OpenTelemetry openTelemetry) {
    this.config = config;
    this.deduplicate = deduplicate;
    this.tracer = openTelemetry.getTracer("ai.verta.reconciler");
  }

  public void start(Reconciler<T> reconciler) {
    if (!config.isTestReconciler()) {
      startResync(reconciler);
    }
    startWorkers(reconciler);
  }

  private void startResync(Reconciler<T> reconciler) {
    Runnable resyncJob =
        () -> {
          var span =
              spanBuilder(reconciler.getClass().getSimpleName() + " resync")
                  .setAttribute(
                      RECONCILER_NAME_ATTRIBUTE_KEY, reconciler.getClass().getSimpleName())
                  .startSpan();
          try (Scope ignore = span.makeCurrent()) {
            reconciler.resync();
          } catch (Exception e) {
            span.setStatus(StatusCode.ERROR);
            span.recordException(e);
            log.error("Failed to resync", e);
          }
        };

    long initialDelayMilliseconds = SECONDS.toMillis(30);
    long resyncPeriodMillis = SECONDS.toMillis(config.getResyncPeriodSeconds());
    RECONCILER_EXECUTOR.submit(
        () -> {
          if (!sleepWithJitter(initialDelayMilliseconds)) {
            return;
          }

          while (true) {
            try {
              resyncJob.run();
            } catch (Exception e) {
              log.error("Resync job failed", e);
            }
            if (!sleepWithJitter(resyncPeriodMillis)) {
              return;
            }
          }
        });
  }

  private SpanBuilder spanBuilder(String spanName) {
    return tracer.spanBuilder(spanName);
  }

  private boolean sleepWithJitter(long milliseconds) {
    try {
      float plusOrMinus20Percent = (random.nextFloat() * 0.4f) - 0.2f;
      long millisWithJitter = (long) (milliseconds * (1f + plusOrMinus20Percent));
      log.trace("sleeping {} milliseconds", millisWithJitter);
      Thread.sleep(millisWithJitter);
      return true;
    } catch (InterruptedException e) {
      Thread.currentThread().interrupt();
      return false;
    }
  }

  private void startWorkers(Reconciler<T> reconciler) {
    for (var i = 0; i < config.getWorkerCount(); i++) {
      Runnable runnable =
          () -> {
            while (true) {
              try {
                if (deduplicate) {
                  Set<T> idsToProcess;
                  // Fetch ids to process while avoiding race conditions
                  try {
                    lock.lock();
                    idsToProcess =
                        pop().stream()
                            .filter(id -> !processingIdSet.contains(id))
                            .collect(Collectors.toSet());
                    if (!idsToProcess.isEmpty()) {
                      processingIdSet.addAll(idsToProcess);
                    }
                  } finally {
                    lock.unlock();
                  }

                  if (!idsToProcess.isEmpty()) {
                    try {
                      traceReconcile(idsToProcess, reconciler);
                    } finally {
                      lock.lock();
                      try {
                        processingIdSet.removeAll(idsToProcess);
                      } finally {
                        lock.unlock();
                      }
                    }
                  }
                } else {
                  traceReconcile(pop(), reconciler);
                }
              } catch (Exception ex) {
                log.error(
                    "Worker for {} reconcile error: ", reconciler.getClass().getSimpleName(), ex);
              }
            }
          };
      RECONCILER_EXECUTOR.execute(runnable);
    }
  }

  private void traceReconcile(Set<T> idsToProcess, Reconciler<T> reconciler) throws Exception {
    var span =
        spanBuilder(reconciler.getClass().getSimpleName() + " reconcile")
            .setAttribute(RECONCILER_NAME_ATTRIBUTE_KEY, reconciler.getClass().getName())
            .setAttribute(NUMBER_OF_ITEMS_ATTRIBUTE_KEY, (long) idsToProcess.size())
            .startSpan();
    try (Scope ignore = span.makeCurrent()) {
      reconciler.reconcile(idsToProcess);
    } catch (Exception e) {
      span.setStatus(StatusCode.ERROR);
      span.recordException(e);
      log.error("Failed to reconcile", e);
    } finally {
      span.end();
    }
  }

  public void insert(T element) {
    lock.lock();
    try {
      if (!elements.contains(element)) {
        elements.add(element);
        order.push(element);
      }
      notEmpty.signal();
    } finally {
      lock.unlock();
    }
  }

  private Set<T> pop() {
    Set<T> ret = new HashSet<>();
    lock.lock();
    try {
      while (elements.isEmpty()) {
        notEmpty.await();
      }

      while (!elements.isEmpty() && ret.size() < config.getBatchSize()) {
        T obj = order.pop();
        elements.remove(obj);
        ret.add(obj);
      }
    } catch (InterruptedException ignored) {
      // Restore interrupted state...
      Thread.currentThread().interrupt();
    } finally {
      lock.unlock();
    }
    return ret;
  }

  public boolean isEmpty() {
    return processingIdSet.isEmpty() && elements.isEmpty();
  }

  // nullables below here
  public static <T> ReconcilerMachine<T> createNull() {
    var reconcilerConfig = ReconcilerConfig.builder().isTestReconciler(true).build();
    return new ReconcilerMachine<>(reconcilerConfig, true, noopOpenTelemetry());
  }
}
