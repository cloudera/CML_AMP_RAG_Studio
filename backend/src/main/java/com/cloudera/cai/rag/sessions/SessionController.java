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

package com.cloudera.cai.rag.sessions;

import com.cloudera.cai.rag.Types.CreateSession;
import com.cloudera.cai.rag.Types.Session;
import com.cloudera.cai.rag.util.UsernameExtractor;
import jakarta.servlet.http.HttpServletRequest;
import java.util.List;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

@RestController
@Slf4j
@RequestMapping("/api/v1/rag/sessions")
public class SessionController {
  private final SessionService sessionService;
  private final UsernameExtractor usernameExtractor = new UsernameExtractor();

  public SessionController(SessionService sessionService) {
    this.sessionService = sessionService;
  }

  @GetMapping(path = "/{id}", produces = "application/json")
  public Session getSession(@PathVariable Long id, HttpServletRequest request) {
    String username = usernameExtractor.extractUsername(request);
    return sessionService.getSessionById(id, username);
  }

  @PostMapping(consumes = "application/json", produces = "application/json")
  public Session create(@RequestBody CreateSession input, HttpServletRequest request) {
    String username = usernameExtractor.extractUsername(request);
    Session toCreate = Session.fromCreateRequest(input, username);
    return sessionService.create(toCreate, username, input);
  }

  @PostMapping(path = "/{id}", consumes = "application/json", produces = "application/json")
  public Session update(@RequestBody Session input, HttpServletRequest request) {
    String username = usernameExtractor.extractUsername(request);
    input = input.withUpdatedById(username);
    return sessionService.update(input, username);
  }

  @DeleteMapping(path = "/{id}")
  public void delete(@PathVariable Long id) {
    sessionService.delete(id);
  }

  @GetMapping(produces = "application/json")
  public List<Session> getSessions(HttpServletRequest request) {
    String username = usernameExtractor.extractUsername(request);
    return sessionService.getSessions(username);
  }
}
