<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ApiError, demoApi } from '@/api'
import { rememberDemo } from '@/demo'

const router = useRouter()
const starting = ref(false)
const error = ref('')

async function startDemo() {
  starting.value = true
  error.value = ''
  try {
    const demo = await demoApi.start()
    rememberDemo(demo)
    await router.push({
      name: 'schedule',
      params: { clubId: String(demo.club_id), token: demo.coordinator_token },
    })
  } catch (e) {
    error.value =
      e instanceof ApiError ? e.message : 'Could not reach the server. Please try again.'
    starting.value = false
  }
}
</script>

<template>
  <main class="landing">
    <section class="hero">
      <p class="eyebrow">Club Shift Scheduler</p>
      <h1>Fair volunteer shifts for amateur sports clubs</h1>
      <p class="lead">
        Members tick the shifts they can do. The app shares them out fairly, so the same few people
        stop doing everything.
      </p>
      <div class="cta">
        <button type="button" :disabled="starting" @click="startDemo">
          {{ starting ? 'Setting up your demo…' : 'Try the demo' }}
        </button>
        <a
          class="link-button button-secondary"
          href="https://github.com/ShawnvanWyngaardt/club-shift-scheduler"
        >
          See the code on GitHub
        </a>
      </div>
      <p v-if="starting" class="muted note">
        The first visit can take up to a minute while the server wakes up.
      </p>
      <p v-if="error" class="error note" role="alert">{{ error }}</p>
      <p class="muted note">
        Your demo is a private club with sample members, deleted after 24 hours. No sign-up.
      </p>
    </section>

    <section aria-labelledby="how-it-works">
      <h2 id="how-it-works">How it works</h2>
      <ol class="steps">
        <li>
          <h3>Members say when they can help</h3>
          <p>
            Everyone gets a personal link. No account and no app to install: open it, tick the
            shifts that suit you, and save.
          </p>
        </li>
        <li>
          <h3>The schedule is shared out fairly</h3>
          <p>
            The coordinator generates a schedule in one click. Members with the fewest points this
            season go first, and any gaps show up straight away.
          </p>
        </li>
        <li>
          <h3>Points keep it fair next time</h3>
          <p>
            Every completed shift earns points, and the less popular the shift, the more it's worth.
            Next round, the people who did the most are asked less.
          </p>
        </li>
      </ol>
    </section>

    <section class="about" aria-labelledby="about">
      <h2 id="about">About this project</h2>
      <p>
        Built by Shawn van Wyngaardt as a hands-on way to learn Python, with FastAPI, Vue 3 and
        PostgreSQL. The plans, decisions and a day-by-day build journal are in the repository.
      </p>
      <p class="links">
        <a
          href="https://github.com/ShawnvanWyngaardt/club-shift-scheduler/tree/main/docs"
          target="blank"
        >
          Read how it was built
        </a>
        <span aria-hidden="true">·</span>
        <a href="/docs" target="blank">API documentation</a>
      </p>
    </section>
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
  border-bottom: 1px solid var(--color-border);
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
