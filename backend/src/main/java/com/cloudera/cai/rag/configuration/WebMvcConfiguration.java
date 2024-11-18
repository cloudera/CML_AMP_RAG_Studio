/*******************************************************************************
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
 * Absent a written agreement with Cloudera, Inc. (“Cloudera”) to the
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
 ******************************************************************************/

package com.cloudera.cai.rag.configuration;

import io.opentelemetry.context.Context;
import io.opentelemetry.context.ContextKey;
import jakarta.servlet.*;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import lombok.extern.slf4j.Slf4j;
import org.slf4j.MDC;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.HandlerInterceptor;
import org.springframework.web.servlet.ModelAndView;
import org.springframework.web.servlet.config.annotation.EnableWebMvc;
import org.springframework.web.servlet.config.annotation.InterceptorRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@EnableWebMvc
@Configuration
@Slf4j
public class WebMvcConfiguration implements WebMvcConfigurer {

  public static final ContextKey<String> REQUEST_ID_CONTEXT_KEY = ContextKey.named("requestId");
  public static final ContextKey<String> ACTOR_CRN_CONTEXT_KEY = ContextKey.named("actorCrn");

  @Override
  public void addInterceptors(InterceptorRegistry registry) {
    registry.addInterceptor(loggingRequestInterceptor()).addPathPatterns("/**");
  }

  private HandlerInterceptor loggingRequestInterceptor() {
    return new HandlerInterceptor() {
      @Override
      public boolean preHandle(
          HttpServletRequest request, HttpServletResponse response, Object handler) {
        MDC.put("requestId", request.getHeader("x-cdp-request-id"));
        MDC.put("actorCrn", request.getHeader("x-cdp-actor-crn"));
        return true;
      }

      @Override
      public void postHandle(
          HttpServletRequest request,
          HttpServletResponse response,
          Object handler,
          ModelAndView modelAndView) {}

      @Override
      public void afterCompletion(
          HttpServletRequest request, HttpServletResponse response, Object handler, Exception ex) {}
    };
  }

  @Bean
  OpenTelemetryHeaderContextWrapper otelFilter() {
    return new OpenTelemetryHeaderContextWrapper();
  }

  public static class OpenTelemetryHeaderContextWrapper implements Filter {
    @Override
    public void doFilter(ServletRequest request, ServletResponse response, FilterChain chain) {
      HttpServletRequest req = (HttpServletRequest) request;
      String requestId = req.getHeader("x-cdp-request-id");
      String actorCrn = req.getHeader("x-cdp-actor-crn");
      Context updatedContext =
          Context.current()
              .with(REQUEST_ID_CONTEXT_KEY, requestId)
              .with(ACTOR_CRN_CONTEXT_KEY, actorCrn);
      updatedContext
          .wrap(
              () -> {
                try {
                  chain.doFilter(request, response);
                } catch (IOException | ServletException e) {
                  throw new RuntimeException(e);
                }
              })
          .run();
    }
  }
}
