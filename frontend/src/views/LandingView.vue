<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { ApiError, demoApi } from "@/api";
import { rememberDemo } from "@/demo";
import HeroSection from "./HeroSection.vue";
import HowItWorks from "./HowItWorks.vue";

const router = useRouter();
const starting = ref(false);
const error = ref("");

async function startDemo() {
  starting.value = true;
  error.value = "";
  try {
    const demo = await demoApi.start();
    rememberDemo(demo);
    await router.push({
      name: "schedule",
      params: { clubId: String(demo.club_id), token: demo.coordinator_token },
    });
  } catch (e) {
    error.value =
      e instanceof ApiError ? e.message : "Could not reach the server. Please try again.";
    starting.value = false;
  }
}
</script>

<template>
  <HeroSection />
  <HowItWorks />
  <main>
    <section class="about" aria-labelledby="about">
      <h2 id="about">About this project</h2>
      <p>
        Built by Shawn van Wyngaardt as a hands-on way to learn Python, with FastAPI, Vue
        3 and PostgreSQL. The plans, decisions and a day-by-day build journal are in the
        repository.
      </p>
      <p class="links">
        <a
          href="https://github.com/ShawnvanWyngaardt/club-shift-scheduler/blob/main/README.md#how-this-was-built"
          target="_blank"
        >
          Read how it was built
        </a>
        <span aria-hidden="true">·</span>
        <a href="/docs" target="_blank">API documentation</a>
      </p>
    </section>
    <div class="cta">
      <button type="button" :disabled="starting" @click="startDemo">
        {{ starting ? "Setting up your demo…" : "Try the demo" }}
      </button>
      <a
        class="link-button button-secondary"
        href="https://github.com/ShawnvanWyngaardt/club-shift-scheduler"
      >
        See the code on GitHub
      </a>
    </div>
  </main>
</template>

<style scoped>
.landing {
  max-width: 720px;
  margin: 0 auto;
  padding: var(--space-6) var(--space-4);
}
.hero {
  padding: var(--space-6) 0;
  margin-bottom: var(--space-6);
}
.eyebrow {
  margin: 0 0 var(--space-2);
  color: var(--color-accent);
  font-weight: 600;
}
h1 {
  font-size: clamp(2rem, 6vw, 2.75rem);
  line-height: 1.15;
  margin-bottom: var(--space-4);
}
.lead {
  font-size: 1.125rem;
  margin: 0 0 var(--space-6);
}
.cta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-3) var(--space-4);
}
.cta p {
  margin: 0;
}
.link-button {
  display: inline-flex;
  align-items: center;
  min-height: 44px;
  padding: 0 var(--space-4);
  border-radius: var(--radius);
  font-weight: 600;
  text-decoration: none;
}
h2 {
  font-size: 1.375rem;
  margin: 0 0 var(--space-4);
}
.steps {
  list-style: none;
  counter-reset: step;
  padding: 0;
  margin: 0 0 var(--space-6);
  display: grid;
  gap: var(--space-4);
}
.steps li {
  counter-increment: step;
  position: relative;
  padding-left: 48px;
}
.steps li::before {
  content: counter(step);
  position: absolute;
  left: 0;
  top: 0;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: var(--color-accent);
  color: #ffffff;
  font-weight: 600;
}
.steps h3 {
  margin: 0 0 var(--space-2);
  font-size: 1.0625rem;
}
.steps p {
  margin: 0;
}
.about {
  padding-top: var(--space-6);
  border-top: 1px solid var(--color-border);
}
.links {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}
.links a {
  color: var(--color-accent);
  font-weight: 600;
}
.note {
  margin: var(--space-3) 0 0;
}
.error {
  color: var(--color-error);
}
</style>
