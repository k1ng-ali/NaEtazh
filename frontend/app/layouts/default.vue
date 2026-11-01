<template>
  <div class="layout">
    <header class="header">
      <div class="container header__inner">
        <NuxtLink to="/" class="header__logo">СтройБаза97</NuxtLink>
        <NuxtLink to="/catalog" class="header__link">Каталог</NuxtLink>
      </div>
    </header>
    <main class="layout__main">
      <slot />
    </main>
  </div>
</template>

<style scoped lang="scss">
.layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;

  &__main {
    flex: 1;
    padding-block: 16px 32px;
  }
}

.header {
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-line);

  &__inner {
    display: flex;
    align-items: center;
    justify-content: space-between;
    min-height: 60px;
  }

  &__logo {
    font-size: 18px;
    font-weight: 700;
  }

  &__link {
    display: flex;
    align-items: center;
    min-height: var(--tap-size);
    font-weight: 500;
  }
}
</style>
