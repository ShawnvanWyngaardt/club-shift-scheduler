<script setup lang="ts">
import lightbulbIcon from "@/assets/landing/lightbulbicon.svg";
import HeroSection from "./HeroSection.vue";
import HowItWorks from "./HowItWorks.vue";
</script>

<template>
  <section class="top-banner">
    <div class="flex justify-center items-center gap-1">
      <img :src="lightbulbIcon" width="28" height="28" />
      <p>Redesign Work In Progress</p>
    </div>
  </section>
  <HeroSection />
  <HowItWorks />
</template>

<style scoped>
.top-banner {
  background-color: var(--color-member-dark-1);
  padding: var(--space-1) var(--space-8);
}
p {
  color: var(--color-text-light);
  font-size: 0.875rem;
  font-style: italic;
  font-weight: 500;
  letter-spacing: 0.0125rem;
  line-height: 1;
}
</style>
