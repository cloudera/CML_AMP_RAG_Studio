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

package com.cloudera.cai.rag.datasources;

import com.cloudera.cai.rag.Types;
import com.cloudera.cai.rag.util.UserTokenCookieDecoder;
import com.cloudera.cai.util.exceptions.BadRequest;
import jakarta.servlet.http.HttpServletRequest;
import java.util.List;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

@RestController
@Slf4j
@RequestMapping("/api/v1/rag/dataSources")
public class RagDataSourceController {
  private final RagDataSourceService dataSourceService;
  private final UserTokenCookieDecoder userTokenCookieDecoder = new UserTokenCookieDecoder();

  @Autowired
  public RagDataSourceController(RagDataSourceService dataSourceService) {
    this.dataSourceService = dataSourceService;
  }

  @PostMapping(consumes = "application/json", produces = "application/json")
  public Types.RagDataSource create(
      @RequestBody Types.RagDataSource input, HttpServletRequest request) {
    log.info("Creating RagDataSource: {}", input);
    if (input.chunkSize() == null || input.chunkSize() < 1) {
      throw new BadRequest("chunkSize must be non-null and greater than 0");
    }
    String username = userTokenCookieDecoder.extractUsername(request.getCookies());
    input = input.withCreatedById(username).withUpdatedById(username);
    return dataSourceService.createRagDataSource(input);
  }

  @PostMapping(value = "/{id}", consumes = "application/json", produces = "application/json")
  public Types.RagDataSource update(
      @RequestBody Types.RagDataSource input, HttpServletRequest request) {
    log.info("Updating RagDataSource: {}", input);
    if (input.name() == null) {
      throw new BadRequest("name must be a non-empty string");
    }
    String username = userTokenCookieDecoder.extractUsername(request.getCookies());
    input = input.withUpdatedById(username);
    return dataSourceService.updateRagDataSource(input);
  }

  @GetMapping(value = "/{id}", produces = "application/json")
  public Types.RagDataSource getRagDataSourceById(@PathVariable Long id) {
    return dataSourceService.getRagDataSourceById(id);
  }

  @DeleteMapping(value = "/{id}")
  public void deleteDataSource(@PathVariable long id) {
    log.info("Deleting DataSource with id: {}", id);
    dataSourceService.deleteDataSource(id);
  }

  @GetMapping(produces = "application/json")
  public List<Types.RagDataSource> getRagDataSources() {
    log.info("Getting all RagDataSources");
    return dataSourceService.getRagDataSources();
  }

  @GetMapping(value = "/{id}/nifiConfig", produces = "application/json")
  public String getNifiConfig(
      @PathVariable Long id, @RequestParam String ragStudioUrl, @RequestParam String configType) {
    return dataSourceService.getNifiConfig(id, ragStudioUrl, configType);
  }
}
