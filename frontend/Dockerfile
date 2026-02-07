FROM node:20-alpine AS base

# 필요한 경우에만 의존성 설치
FROM base AS deps
# libc6-compat이 왜 필요한지 이해하려면 https://github.com/nodejs/docker-node/tree/b4117f9333da4138b03a546ec926ef50a31506c3#nodealpine 참고
RUN apk add --no-cache libc6-compat
WORKDIR /app

# 선호하는 패키지 관리자를 기반으로 의존성 설치
COPY package.json package-lock.json* ./
RUN npm ci

# 소스 코드가 변경되었을 때만 재빌드
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Next.js는 기본적으로 표준 출력으로 컴파일됨. 
# 빌드 중 텔레메트리(telemetry) 비활성화.
ENV NEXT_TELEMETRY_DISABLED 1

ARG NEXT_PUBLIC_API_BASE_URL
ENV NEXT_PUBLIC_API_BASE_URL=$NEXT_PUBLIC_API_BASE_URL

RUN npm run build

# 프로덕션 이미지, 모든 파일을 복사하고 next 실행
FROM base AS runner
WORKDIR /app

ENV NODE_ENV production
# 런타임에 텔레메트리를 비활성화하려면 다음 줄의 주석을 해제하세요.
# ENV NEXT_TELEMETRY_DISABLED 1

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public

# 이미지 크기를 줄이기 위해 출력 추적(output traces)을 자동으로 활용
# https://nextjs.org/docs/advanced-features/output-file-tracing
# 참고: 여기서는 standalone 출력을 완전히 사용하지 않는 표준 "npm run start"를 사용하므로,
# 필요한 디렉토리를 복사합니다. next.config.js에서 'output: "standalone"'이 활성화된 경우 .next/standalone을 복사해야 합니다.
# 현재는 설정 변경을 최소화하기 위해 표준 빌드 방식을 유지합니다.

COPY --from=builder --chown=nextjs:nodejs /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json

USER nextjs

EXPOSE 3000

ENV PORT 3000
# 호스트네임을 localhost로 설정
ENV HOSTNAME "0.0.0.0"

CMD ["npm", "run", "start"]
