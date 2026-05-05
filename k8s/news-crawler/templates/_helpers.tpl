{{- define "news-crawler.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "news-crawler.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name (include "news-crawler.name" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}

{{- define "news-crawler.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" -}}
{{- end -}}

{{- define "news-crawler.selectorLabels" -}}
app.kubernetes.io/name: {{ include "news-crawler.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{- define "news-crawler.labels" -}}
helm.sh/chart: {{ include "news-crawler.chart" . }}
{{ include "news-crawler.selectorLabels" . }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}

{{- define "news-crawler.backend.fullname" -}}
{{- printf "%s-backend" (include "news-crawler.fullname" .) -}}
{{- end -}}

{{- define "news-crawler.frontend.fullname" -}}
{{- printf "%s-frontend" (include "news-crawler.fullname" .) -}}
{{- end -}}

{{- define "news-crawler.postgres.fullname" -}}
{{- printf "%s-postgres" (include "news-crawler.fullname" .) -}}
{{- end -}}

{{- define "news-crawler.elasticsearch.fullname" -}}
{{- printf "%s-elasticsearch" (include "news-crawler.fullname" .) -}}
{{- end -}}

{{- define "news-crawler.kibana.fullname" -}}
{{- printf "%s-kibana" (include "news-crawler.fullname" .) -}}
{{- end -}}

{{- define "news-crawler.backend.configmapName" -}}
{{- printf "%s-config" (include "news-crawler.backend.fullname" .) -}}
{{- end -}}

{{- define "news-crawler.backend.secretName" -}}
{{- printf "%s-secret" (include "news-crawler.backend.fullname" .) -}}
{{- end -}}

{{- define "news-crawler.postgres.secretName" -}}
{{- printf "%s-secret" (include "news-crawler.postgres.fullname" .) -}}
{{- end -}}

{{- define "news-crawler.elasticsearch.url" -}}
{{- if .Values.backend.config.elasticsearchUrl -}}
{{- .Values.backend.config.elasticsearchUrl -}}
{{- else if .Values.elasticsearch.enabled -}}
{{- printf "http://%s:%v" (include "news-crawler.elasticsearch.fullname" .) .Values.elasticsearch.service.port -}}
{{- else -}}
{{- required "Set backend.config.elasticsearchUrl when elasticsearch.enabled=false" .Values.backend.config.elasticsearchUrl -}}
{{- end -}}
{{- end -}}

{{- define "news-crawler.database.url" -}}
{{- if .Values.backend.secret.databaseUrl -}}
{{- .Values.backend.secret.databaseUrl -}}
{{- else if .Values.postgres.enabled -}}
{{- printf "postgresql+asyncpg://%s:%s@%s:%v/%s" .Values.postgres.username .Values.postgres.password (include "news-crawler.postgres.fullname" .) .Values.postgres.service.port .Values.postgres.database -}}
{{- else -}}
{{- required "Set backend.secret.databaseUrl when postgres.enabled=false" .Values.backend.secret.databaseUrl -}}
{{- end -}}
{{- end -}}