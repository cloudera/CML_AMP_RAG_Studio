# ----- RAG API BUILDER -----
FROM docker-private.infra.cloudera.com/cloudera_base/ubi8/openjdk-21:1.20-3 AS rag_api_builder
RUN pwd
RUN mkdir build
COPY --chown=jboss *gradle* /tmp/build/
ADD --chown=jboss gradle /tmp/build/gradle
WORKDIR /tmp/build

# run this to make sure the wrapper code is downloaded
RUN ./gradlew tasks

# run this to download dependencies in a separate layer
RUN ./gradlew dependencies

COPY --chown=jboss . /home/jboss/build/
WORKDIR /home/jboss/build
RUN ./gradlew bootJar

# ----- RAG API FINAL -----
FROM docker-private.infra.cloudera.com/cloudera_base/ubi8/cldr-openjdk-21-runtime-cis:1.20-2-stig-19062024 AS rag_api_final
RUN mkdir app
COPY --from=rag_api_builder /home/jboss/build/build/libs/rag-api.jar /app/

ENTRYPOINT ["java", "-jar","/app/rag-api.jar"]
