{{/*
Expand the name of the chart.
*/}}
{{- define "eafix-trading.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "eafix-trading.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "eafix-trading.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "eafix-trading.labels" -}}
helm.sh/chart: {{ include "eafix-trading.chart" . }}
{{ include "eafix-trading.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: eafix-trading-system
{{- end }}

{{/*
Selector labels
*/}}
{{- define "eafix-trading.selectorLabels" -}}
app.kubernetes.io/name: {{ include "eafix-trading.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Service selector labels for individual services
*/}}
{{- define "eafix-trading.serviceSelectorLabels" -}}
app.kubernetes.io/name: {{ . }}
app.kubernetes.io/instance: {{ $.Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "eafix-trading.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "eafix-trading.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Return the proper image name
*/}}
{{- define "eafix-trading.image" -}}
{{- $registryName := .Values.image.registry -}}
{{- $repositoryName := .Values.image.repository -}}
{{- $separator := "/" -}}
{{- if .Values.global }}
    {{- if .Values.global.imageRegistry }}
        {{- $registryName = .Values.global.imageRegistry -}}
    {{- end -}}
{{- end -}}
{{- if $registryName }}
    {{- printf "%s%s%s" $registryName $separator $repositoryName -}}
{{- else }}
    {{- printf "%s" $repositoryName -}}
{{- end -}}
{{- end -}}

{{/*
Return the proper image name for a specific service
*/}}
{{- define "eafix-trading.serviceImage" -}}
{{- $registryName := .Values.image.registry -}}
{{- $repositoryName := .Values.image.repository -}}
{{- $separator := "/" -}}
{{- $tag := .Values.image.tag | toString -}}
{{- if .Values.global }}
    {{- if .Values.global.imageRegistry }}
        {{- $registryName = .Values.global.imageRegistry -}}
    {{- end -}}
{{- end -}}
{{- if $registryName }}
    {{- printf "%s%s%s/%s:%s" $registryName $separator $repositoryName .serviceName $tag -}}
{{- else }}
    {{- printf "%s/%s:%s" $repositoryName .serviceName $tag -}}
{{- end -}}
{{- end -}}

{{/*
Return the proper Docker Image Registry Secret Names
*/}}
{{- define "eafix-trading.imagePullSecrets" -}}
{{- include "common.images.pullSecrets" (dict "images" (list .Values.image) "global" .Values.global) -}}
{{- end -}}

{{/*
Return the storage class name
*/}}
{{- define "eafix-trading.storageClass" -}}
{{- if .Values.global -}}
    {{- if .Values.global.storageClass -}}
        {{- if (eq "-" .Values.global.storageClass) -}}
            {{- printf "storageClassName: \"\"" -}}
        {{- else }}
            {{- printf "storageClassName: %s" .Values.global.storageClass -}}
        {{- end -}}
    {{- else -}}
        {{- if .Values.persistence.storageClass -}}
              {{- if (eq "-" .Values.persistence.storageClass) -}}
                  {{- printf "storageClassName: \"\"" -}}
              {{- else }}
                  {{- printf "storageClassName: %s" .Values.persistence.storageClass -}}
              {{- end -}}
        {{- end -}}
    {{- end -}}
{{- else -}}
    {{- if .Values.persistence.storageClass -}}
        {{- if (eq "-" .Values.persistence.storageClass) -}}
            {{- printf "storageClassName: \"\"" -}}
        {{- else }}
            {{- printf "storageClassName: %s" .Values.persistence.storageClass -}}
        {{- end -}}
    {{- end -}}
{{- end -}}
{{- end -}}

{{/*
Create environment variables for Redis connection
*/}}
{{- define "eafix-trading.redisEnv" -}}
- name: SERVICE_REDIS_URL
  value: {{ .Values.environment.redisUrl | quote }}
- name: REDIS_PASSWORD
  valueFrom:
    secretKeyRef:
      name: trading-secrets
      key: REDIS_PASSWORD
{{- end -}}

{{/*
Create environment variables for PostgreSQL connection
*/}}
{{- define "eafix-trading.postgresEnv" -}}
- name: SERVICE_POSTGRES_URL
  value: {{ .Values.environment.postgresUrl | quote }}
- name: POSTGRES_USER
  valueFrom:
    secretKeyRef:
      name: trading-secrets
      key: POSTGRES_USER
- name: POSTGRES_PASSWORD
  valueFrom:
    secretKeyRef:
      name: trading-secrets
      key: POSTGRES_PASSWORD
- name: POSTGRES_DB
  valueFrom:
    secretKeyRef:
      name: trading-secrets
      key: POSTGRES_DB
{{- end -}}

{{/*
Create common environment variables
*/}}
{{- define "eafix-trading.commonEnv" -}}
- name: SERVICE_LOG_LEVEL
  value: {{ .Values.environment.logLevel | quote }}
{{- include "eafix-trading.redisEnv" . }}
{{- end -}}

{{/*
Create resource limits
*/}}
{{- define "eafix-trading.resources" -}}
{{- $serviceName := . -}}
{{- $resources := $.Values.resources.default -}}
{{- if hasKey $.Values.resources $serviceName -}}
    {{- $resources = index $.Values.resources $serviceName -}}
{{- end -}}
resources:
  {{- toYaml $resources | nindent 2 }}
{{- end -}}

{{/*
Create standard health checks
*/}}
{{- define "eafix-trading.healthChecks" -}}
livenessProbe:
  httpGet:
    path: /healthz
    port: {{ .port }}
  initialDelaySeconds: {{ .Values.healthcheck.initialDelaySeconds }}
  periodSeconds: {{ .Values.healthcheck.periodSeconds }}
  timeoutSeconds: {{ .Values.healthcheck.timeoutSeconds }}
  failureThreshold: {{ .Values.healthcheck.failureThreshold }}
readinessProbe:
  httpGet:
    path: /healthz
    port: {{ .port }}
  initialDelaySeconds: 5
  periodSeconds: 5
  timeoutSeconds: {{ .Values.healthcheck.timeoutSeconds }}
  failureThreshold: {{ .Values.healthcheck.failureThreshold }}
{{- end -}}

{{/*
Create security context
*/}}
{{- define "eafix-trading.securityContext" -}}
securityContext:
  {{- toYaml .Values.securityContext | nindent 2 }}
{{- end -}}

{{/*
Create pod security context
*/}}
{{- define "eafix-trading.podSecurityContext" -}}
securityContext:
  {{- toYaml .Values.podSecurityContext | nindent 2 }}
{{- end -}}