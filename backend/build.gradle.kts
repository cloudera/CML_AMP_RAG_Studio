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
 */

import org.springframework.boot.gradle.plugin.SpringBootPlugin

plugins {
    java
    id("org.springframework.boot") version "3.3.3"
    id("com.diffplug.spotless") version "6.25.0"
}

repositories {
    mavenCentral()
}

apply(plugin = "com.diffplug.spotless")

val otelCoreVersion = "1.41.0"
val otelInstrumentationVersion = "2.6.0"

dependencies {
    // boms
    implementation(platform("io.opentelemetry.instrumentation:opentelemetry-instrumentation-bom:$otelInstrumentationVersion"))
    implementation(platform("io.opentelemetry.instrumentation:opentelemetry-instrumentation-bom-alpha:$otelInstrumentationVersion-alpha"))
    implementation(platform("io.opentelemetry:opentelemetry-bom:$otelCoreVersion"))
    implementation(platform("io.opentelemetry:opentelemetry-bom-alpha:$otelCoreVersion-alpha"))
    implementation(platform(SpringBootPlugin.BOM_COORDINATES))
    implementation(platform("software.amazon.awssdk:bom:2.27.12"))
    developmentOnly("org.springframework.boot:spring-boot-devtools:3.3.3")

    // standard dependencies
    runtimeOnly("com.h2database:h2:2.2.224")
    runtimeOnly("org.postgresql:postgresql:42.7.3")
    implementation("org.jdbi:jdbi3-core:3.45.2")
    implementation("org.jdbi:jdbi3-jackson2:3.45.2")
    implementation("com.zaxxer:HikariCP:5.1.0")
    implementation("javax.annotation:javax.annotation-api:1.3.2")
    implementation("org.springframework.boot:spring-boot-starter-web")
    // swagger UI available at http://localhost:8080/swagger-ui/index.html
    implementation("org.springdoc:springdoc-openapi-starter-webmvc-ui:2.2.0")

    implementation("software.amazon.awssdk:s3")
    implementation("software.amazon.awssdk:sts")
    implementation("software.amazon.awssdk:apache-client")
    compileOnly("org.projectlombok:lombok:1.18.34")
    annotationProcessor("org.projectlombok:lombok:1.18.34")
    testCompileOnly("org.projectlombok:lombok:1.18.34")
    testAnnotationProcessor("org.projectlombok:lombok:1.18.34")

    implementation("io.opentelemetry.instrumentation:opentelemetry-instrumentation-annotations")
    runtimeOnly("io.opentelemetry.instrumentation:opentelemetry-logback-mdc-1.0")
    implementation("io.opentelemetry.instrumentation:opentelemetry-java-http-client")
    implementation("io.opentelemetry:opentelemetry-api")

    // testing dependencies
    testImplementation("org.springframework.boot:spring-boot-starter-test")
    testRuntimeOnly("org.junit.platform:junit-platform-launcher")
    testImplementation("org.awaitility:awaitility:4.2.2")
}

tasks.named<Test>("test") {
    useJUnitPlatform()

    maxHeapSize = "1G"

    testLogging {
        events("passed")
    }
    
    // Clean environment for tests - exclude problematic environment variables
    environment.remove("DB_URL")
    environment.remove("DB_TYPE")
    environment.remove("VECTOR_DB_PROVIDER")
    
    // Ensure tests use clean in-memory H2 database
    systemProperty("spring.test.database.replace", "any")
    systemProperty("spring.datasource.url", "jdbc:h2:mem:testdb")
}

tasks {
    named<JavaCompile>("compileJava") {
        dependsOn("spotlessApply")
    }
}


spotless {
    java {
        googleJavaFormat("1.23.0")
    }
}

springBoot {
    mainClass.set("com.cloudera.cai.RagApiMain")
}
