<script setup lang="ts">
defineProps<{ hint?: string }>()
</script>

<template>
  <main class="page">
    <h1>Congratulations! You found the error page.</h1>
    <p class="muted">{{ hint ?? "This page doesn't exist or the link is incomplete." }}</p>
    <p>
      If the above doesn't provide you with any comfort or way forward, it was James who deleted it
      and we are looking to fire him. Or put him on toilet duty at your club.
    </p>

    <h2>How do I see any progress on the App you ask...</h2>
    <p class="muted">
      While still in its early versions, you're welcome to have a look at the following
      <a
        href="https://github.com/ShawnvanWyngaardt/club-shift-scheduler/blob/main/README.md"
        target="_blank"
        >README file</a
      >
      to learn more.
    </p>
    <p>Thank you for taking the time to come and visit my project.</p>
    <p>
      Feel free to get in touch with me for any questions or suggestions via my
      <a href="https://www.linkedin.com/in/shawn-van-wyngaardt/" target="_blank">LinkedIn</a>.
    </p>
  </main>
</template>
