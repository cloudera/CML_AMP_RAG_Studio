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

import lombok.Value;

@Value
public class Migration implements Comparable<Migration> {
  public static final String ENABLE_MIGRATIONS_ENV_VAR = "LIQUIBASE_MIGRATION";
  public static final String RUN_MIGRATIONS_SEPARATELY = "RUN_LIQUIBASE_SEPARATE";

  String filename;

  @Override
  public int compareTo(Migration o) {
    int versionDiff = this.getNumber() - o.getNumber();
    if (versionDiff == 0) {
      if (this.isUp() && o.isUp()) {
        return 0;
      }
      if (this.isDown()) {
        return 1;
      }
      return -1;
    }
    return versionDiff;
  }

  int getNumber() {
    String[] pieces = filename.split("_");
    return Integer.parseInt(pieces[0]);
  }

  /**
   * An "up" migration could also be called the "forward" migration. It is the migration that
   * applies a change to an existing database.
   */
  boolean isUp() {
    String[] pieces = filename.split("\\.");
    return "up".equals(pieces[1]);
  }

  /**
   * A "down" migration could also be called the "reverse" migration. It is the migration that
   * reverts the change from the corresponding "up" migration.
   */
  boolean isDown() {
    String[] pieces = filename.split("\\.");
    return "down".equals(pieces[1]);
  }
}
