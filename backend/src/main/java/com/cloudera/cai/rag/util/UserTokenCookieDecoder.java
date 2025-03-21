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

package com.cloudera.cai.rag.util;

import static com.fasterxml.jackson.databind.DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES;

import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.servlet.http.Cookie;
import java.util.Base64;
import lombok.extern.slf4j.Slf4j;

@Slf4j
public class UserTokenCookieDecoder {
  public static final String USER_TOKEN_COOKIE_NAME = "_basusertoken";
  private final ObjectMapper objectMapper =
      new ObjectMapper().configure(FAIL_ON_UNKNOWN_PROPERTIES, false);

  // note: switch to getting these from headers
  //  remote-user-perm
  //  remote-user

  public String extractUsername(Cookie[] cookies) {
    if (cookies != null) {
      for (Cookie cookie : cookies) {
        if (USER_TOKEN_COOKIE_NAME.equals(cookie.getName())) {
          try {
            var rawJwt = cookie.getValue();
            var pieces = rawJwt.split("\\.");
            if (pieces.length != 3) {
              log.warn("Invalid JWT cookie: {}", rawJwt);
              return "unknown";
            }
            Base64.Decoder decoder = Base64.getDecoder();
            var decodedUserInfo = decoder.decode(pieces[1]);
            JwtCookie jwtCookie = objectMapper.readValue(decodedUserInfo, JwtCookie.class);
            log.info("Extracted username from cookie: {}", jwtCookie.username());
            return jwtCookie.username();
          } catch (Exception e) {
            log.warn("Failed to extract username from cookie", e);
          }
        }
      }
    }
    return "unknown";
  }

  record JwtCookie(String username) {}
}
