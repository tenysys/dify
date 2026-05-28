'use client'

import { Button } from '@langgenius/dify-ui/button'
import { useEffect, useRef, useState } from 'react'
import Loading from '@/app/components/base/loading'
import { useRouter, useSearchParams } from '@/next/navigation'
import { storeConsoleAuthTokens } from '@/service/console-auth'

const getHashParams = () => {
  const hash = globalThis.location.hash.startsWith('#')
    ? globalThis.location.hash.slice(1)
    : globalThis.location.hash
  return new URLSearchParams(hash)
}

export default function OAuthSigninPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const hasStartedRef = useRef(false)
  const [errorMessage, setErrorMessage] = useState('')

  useEffect(() => {
    if (hasStartedRef.current)
      return

    hasStartedRef.current = true

    const hashParams = getHashParams()
    const accessToken = hashParams.get('access_token') || ''
    const refreshToken = hashParams.get('refresh_token') || ''
    const csrfToken = hashParams.get('csrf_token') || ''

    if (!accessToken || !refreshToken || !csrfToken) {
      setErrorMessage('Missing OAuth tokens.')
      return
    }

    storeConsoleAuthTokens({
      access_token: accessToken,
      refresh_token: refreshToken,
      csrf_token: csrfToken,
    })

    const inviteToken = searchParams.get('invite_token')
    if (inviteToken) {
      const query = searchParams.toString()
      router.replace(query ? `/signin/invite-settings?${query}` : '/signin/invite-settings')
      return
    }

    router.replace('/apps')
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
          <h2 className="title-2xl-semi-bold text-text-primary">OAuth sign-in failed</h2>
          <p className="mt-2 body-md-regular text-text-tertiary">{errorMessage}</p>
          <Button
            className="mt-6 w-full"
            variant="primary"
            onClick={() => router.replace('/signin')}
          >
            Back to sign in
          </Button>
        </div>
      </div>
    </div>
  )
}
