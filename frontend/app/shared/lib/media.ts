// Свои фото API отдаёт путём /media/..., чужие ссылки приходят полными
export const useMediaUrl = () => {
  const { mediaUrl } = useRuntimeConfig().public
  return (path: string) => (path.startsWith('/') ? `${mediaUrl}${path}` : path)
}
