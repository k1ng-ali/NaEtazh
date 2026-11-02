export type ToastType = 'success' | 'error'

export interface Toast {
  id: number
  type: ToastType
  text: string
}

// Короткие уведомления админки внизу экрана
export const useToast = () => {
  const toasts = useState<Toast[]>('admin-toasts', () => [])

  function show(text: string, type: ToastType = 'success', ms = 3500) {
    const id = Date.now() + Math.random()
    toasts.value = [...toasts.value, { id, type, text }]
    setTimeout(() => {
      toasts.value = toasts.value.filter((toast) => toast.id !== id)
    }, ms)
  }

  return {
    toasts,
    success: (text: string) => show(text, 'success'),
    error: (text: string) => show(text, 'error', 6000),
  }
}
