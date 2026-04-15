<template>
  <header class="content-header">
    <div class="content-leading">
      <slot name="leading" />
    </div>
    <h1 class="content-title">{{ title }}</h1>
    <div class="content-actions">
      <slot name="actions" />
    </div>
  </header>
</template>

<script setup lang="ts">
defineProps<{
  title: string
}>()
</script>

<style scoped>
@reference "tailwindcss";

.content-header {
  @apply relative z-10 w-full min-h-12 sm:min-h-14 flex items-center gap-2 sm:gap-3 px-2 sm:px-3 pt-3 sm:pt-4 pb-2 bg-white;
}

.content-title {
  @apply m-0 min-w-0 flex-1 truncate text-sm font-medium leading-6 text-slate-900 max-sm:text-xs;
}

.content-actions {
  @apply flex items-center justify-end gap-1;
}

.content-leading {
  @apply flex items-center gap-1;
}

@media (max-width: 639px) {
  .content-header {
    @apply min-h-10 gap-1.5 px-2 pt-1.5 pb-1;
  }

  .content-title {
    @apply text-[14px] font-semibold leading-5;
  }

  .content-leading,
  .content-actions {
    @apply shrink-0;
  }

  .content-actions {
    @apply gap-0;
  }
}
</style>
