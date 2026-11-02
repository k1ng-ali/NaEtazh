// Ответы API на английском, менеджеру показываем по-русски
const MESSAGES: Record<string, string> = {
  'Invalid login or password': 'Неверный логин или пароль',
  'Session expired': 'Сессия закончилась, войдите снова',
  'Not enough rights': 'Недостаточно прав',
  'Category not found': 'Категория не найдена',
  'Category slug already exists': 'Такой адрес категории уже есть',
  'Category has products': 'В категории есть товары. Сначала перенесите их',
  'Category has subcategories': 'В категории есть подкатегории',
  'Category cannot be its own parent': 'Категория не может быть вложена сама в себя',
  'Product not found': 'Товар не найден',
  'Product sku already exists': 'Такой артикул уже есть',
  'Product SKU already exists': 'Такой артикул уже есть',
  'Product slug already exists': 'Такой адрес товара уже есть',
  'Too many images': 'Не больше 10 фото у товара',
  'File is not a valid image': 'Файл не похож на фото',
  'Unsupported image format': 'Подходят только JPG, PNG и WebP',
  'Image is larger than 10 MB': 'Фото больше 10 МБ',
  'Quantity is less than reserved': 'Остаток меньше, чем уже зарезервировано под заказы',
  'Warehouse not found': 'Склад не найден',
  'Offer already linked': 'Предложение уже привязано к товару',
  'Sync already running': 'Импорт уже идёт, подождите',
}

export const errorMessage = (error: unknown, fallback = 'Что-то пошло не так. Попробуйте ещё раз'): string => {
  const data = (error as { data?: { detail?: unknown } })?.data
  if (typeof data?.detail === 'string') return MESSAGES[data.detail] ?? fallback
  if (Array.isArray(data?.detail)) return 'Проверьте заполнение полей'
  if ((error as { response?: unknown })?.response === undefined) return 'Нет связи с сервером'
  return fallback
}
