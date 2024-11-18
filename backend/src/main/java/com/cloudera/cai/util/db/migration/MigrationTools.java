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

package com.cloudera.cai.util.db.migration;

import java.nio.charset.StandardCharsets;
import java.sql.SQLException;
import java.util.zip.CRC32;
import lombok.extern.slf4j.Slf4j;

@Slf4j
class MigrationTools {
  private static final int MAX_LOCK_TRIES = 15;

  static String generateLockId(String database, String otherLockInfo) {
    CRC32 crc32 = new CRC32();
    crc32.update((database + ":" + otherLockInfo).getBytes(StandardCharsets.UTF_8));
    return String.valueOf(crc32.getValue());
  }

  static void lockDatabase(MigrationDatastore datastore) throws MigrationException {
    int tries = 0;
    while (tries++ < MAX_LOCK_TRIES) {
      try {
        datastore.lock();
        return;
      } catch (SQLException e) {
        log.warn("failed to lock db. sleeping 1s then trying again. message: " + e.getMessage());
        try {
          Thread.sleep(1000);
        } catch (InterruptedException ex) {
          Thread.currentThread().interrupt();
          log.warn("Interrupted while trying to lock the database. Returning");
          return;
        }
      }
    }
    throw new MigrationException("Failed to lock the database for migrations.");
  }
}
