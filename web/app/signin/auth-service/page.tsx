'use client'

import type { ResponseError } from '@/service/fetch'
import { Button } from '@langgenius/dify-ui/button'
import { toast } from '@langgenius/dify-ui/toast'
import { useEffect, useRef, useState } from 'react'
import Loading from '@/app/components/base/loading'
import {
  AUTH_SERVICE_TOKEN_PARAM,
} from '@/config'
import { useRouter, useSearchParams } from '@/next/navigation'
import { authServiceLogin } from '@/service/common'
import { resolvePostLoginRedirect } from '../utils/post-login-redirect'

const getHashParams = () => {
  const hash = globalThis.location.hash.startsWith('#')
    ? globalThis.location.hash.slice(1)
    : globalThis.location.hash
  return new URLSearchParams(hash)
}

const getAuthServiceToken = (searchParams: URLSearchParams) => {
  return searchParams.get(AUTH_SERVICE_TOKEN_PARAM)
    || searchParams.get('access_token')
    || getHashParams().get(AUTH_SERVICE_TOKEN_PARAM)
    || getHashParams().get('access_token')
    || ''
}

const getSanitizedParams = (searchParams: URLSearchParams) => {
  searchParams.delete(AUTH_SERVICE_TOKEN_PARAM)
  searchParams.delete('access_token')
  return searchParams
}

export default function AuthServiceSigninPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const hasStartedRef = useRef(false)
  const [errorMessage, setErrorMessage] = useState('')
  const backToSigninUrl = (() => {
    const params = getSanitizedParams(new URLSearchParams(searchParams.toString()))
    const query = params.toString()
    return query ? `/signin?${query}` : '/signin'
  })()

  useEffect(() => {
    if (hasStartedRef.current)
      return

    hasStartedRef.current = true

    const run = async () => {
      const token = getAuthServiceToken(new URLSearchParams(searchParams.toString()))
      if (!token) {
        setErrorMessage('Missing auth-service token.')
        return
      }

      try {
        const result = await authServiceLogin(token)
        if (result.result !== 'success') {
          setErrorMessage(result.data || 'Auth-service sign-in failed.')
          return
        }

        const preservedParams = getSanitizedParams(new URLSearchParams(searchParams.toString()))
        const inviteToken = preservedParams.get('invite_token')
        if (inviteToken) {
          const query = preservedParams.toString()
          router.replace(query ? `/signin/invite-settings?${query}` : '/signin/invite-settings')
          return
        }

        const redirectUrl = resolvePostLoginRedirect(searchParams)
        router.replace(redirectUrl || '/apps')
      }
      catch (error) {
        const responseError = error as ResponseError
        const message = responseError.message || 'Auth-service sign-in failed.'
        toast.error(message)
        setErrorMessage(message)
      }
    }

    run()
  }, [router, searchParams])

  if (!errorMessage) {
    return (
      <div className="flex w-full grow flex-col items-center justify-center px-6 md:px-[108px]">
        <Loading type="area" />
      </div>
    )
  }

  return (
    <div className="flex w-full grow flex-col items-center justify-center px-6 md:px-[108px]">
      <div className="w-full max-w-md rounded-2xl border border-components-panel-border-subtle bg-components-panel-bg shadow-lg">
        <div className="p-6">
          <h2 className="title-2xl-semi-bold text-text-primary">Auth-service sign-in failed</h2>
          <p className="mt-2 body-md-regular text-text-tertiary">{errorMessage}</p>
          <Button
            className="mt-6 w-full"
            variant="primary"
            onClick={() => router.replace(backToSigninUrl)}
          >
            Back to sign in
          </Button>
        </div>
      </div>
    </div>
  )
}
