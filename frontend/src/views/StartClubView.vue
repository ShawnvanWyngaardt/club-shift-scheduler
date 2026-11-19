<script setup lang="ts">
import '@/assets/coordinator.css'
import { computed, ref } from 'vue'
import { ApiError, coordinatorApi, type ClubWithToken } from '@/api'
import { useStartDemo } from '@/composables/useStartDemo'
import { coordinatorUrl, copyText, saveForYourself } from '@/links'

const name = ref('')
const club = ref<ClubWithToken | null>(null)
const creating = ref(false)
const error = ref('')
const copied = ref(false)
const saved = ref(false) // "I've saved my link": unlocks the next step

const { phase: demoPhase, isBusy: demoBusy, startDemo } = useStartDemo()

const link = computed(() =>
  club.value ? coordinatorUrl(club.value.id, club.value.coordinator_token) : '',
)
const sendTo = computed(() => (club.value ? saveForYourself(club.value.name, link.value) : null))

async function create() {
  creating.value = true
  error.value = ''
  try {
    club.value = await coordinatorApi.createClub(name.value.trim())
  } catch (e) {
    error.value =
      e instanceof ApiError ? e.message : 'Could not reach the server. Please try again.'
  } finally {
    creating.value = false
  }
}

async function copy() {
  copied.value = await copyText(link.value)
}

const demoText = computed(
  () =>
    ({
      idle: 'Try the demo instead',
      starting: 'Starting the demo…',
      waking: 'Waking the server, a few more seconds…',
      full: 'Too many demos right now. Try again later.',
      failed: "Couldn't start the demo. Try again.",
    })[demoPhase.value],
)
</script>

<template>
  <div class="coord">
    <main class="wrap start">
      <span class="eyebrow">Coordinator</span>

      <!-- Step 1: name the club -->
      <template v-if="!club">
        <div class="page-head">
          <div>
            <h1>Start a club</h1>
            <p>
              You'll be its coordinator: you plan the shifts, and members pick the ones they can
              do. No account needed.
            </p>
          </div>
        </div>

        <form class="card" @submit.prevent="create">
          <label for="club-name" class="field-label">Club name</label>
          <div class="add">
            <input
              id="club-name"
              v-model="name"
              type="text"
              required
              maxlength="100"
              placeholder="For example VV Oranje"
            />
            <button type="submit" class="btn btn-primary" :disabled="creating || !name.trim()">
              {{ creating ? 'Creating…' : 'Create club' }}
            </button>
          </div>
          <p v-if="error" class="error" role="alert">{{ error }}</p>
        </form>

        <p class="aside">
          Just looking?
          <button type="button" class="text-link" :disabled="demoBusy()" @click="startDemo">
            {{ demoText }}</button
          >: a private sample club with members and shifts, gone after 24 hours.
        </p>
      </template>

      <!-- Step 2: keep the link. It's the only way back in. -->
      <template v-else>
        <div class="page-head">
          <div>
            <h1>{{ club.name }} is ready</h1>
            <p>One thing before you add your members.</p>
          </div>
        </div>

        <section class="card save" aria-labelledby="save-title">
          <h2 id="save-title">Save your coordinator link now</h2>
          <p>
            This link is the only way into your club's coordinator screens. There are no accounts
            and no password reset, so it can't be sent again. Keep it somewhere you'll find it.
          </p>

          <label for="coordinator-link" class="field-label">Your coordinator link</label>
          <div class="add">
            <input
              id="coordinator-link"
              class="mono"
              :value="link"
              type="text"
              readonly
              @focus="($event.target as HTMLInputElement).select()"
            />
            <button type="button" class="btn btn-primary" @click="copy">
              {{ copied ? 'Copied' : 'Copy link' }}
            </button>
          </div>

          <p class="send">Or send it to yourself:</p>
          <div class="btn-row">
            <a
              class="btn btn-small btn-whatsapp"
              :href="sendTo?.whatsapp"
              target="_blank"
              rel="noopener"
            >
              WhatsApp<span class="sr-only"> (opens in a new tab)</span>
            </a>
            <a class="btn btn-small btn-ghost" :href="sendTo?.email">Email</a>
          </div>

          <label class="confirm">
            <input v-model="saved" type="checkbox" />
            I've saved my link somewhere safe
          </label>
          <RouterLink
            v-if="saved"
            class="btn btn-go"
            :to="{
              name: 'members',
              params: { clubId: String(club.id), token: club.coordinator_token },
            }"
          >
            Add your members
          </RouterLink>
          <button v-else type="button" class="btn btn-go" disabled>Add your members</button>
        </section>
      </template>
    </main>
  </div>
</template>

<style scoped>
/* One task, so a narrow page. Specific enough to beat the shared .coord .wrap width. */
main.wrap.start {
  max-width: 640px;
}
.eyebrow {
  display: block;
  margin-bottom: 8px;
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--sky);
}
.card {
  display: grid;
  gap: 8px;
  padding: 20px;
  background: var(--surface);
  border-radius: var(--r);
  border-right: 3px solid var(--navy);
  box-shadow: var(--shadow);
}
.card h2 {
  margin: 0;
  font-size: 18px;
}
.card p {
  margin: 0 0 8px;
  font-size: 14px;
}
.field-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--muted);
}
.add {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.add input {
  flex: 1;
  min-width: 0;
  min-height: 40px;
  padding: 0 12px;
  border: 1.5px solid var(--line);
  border-radius: 12px;
  background: var(--surface);
  color: var(--ink);
  font: inherit;
  font-size: 14px;
}
.add input.mono {
  font-family: var(--font-mono);
  font-size: 13px;
}
.send {
  margin: 8px 0 0;
  font-size: 13px;
  color: var(--muted);
}
.confirm {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 16px 0 4px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
}
.confirm input {
  width: 18px;
  height: 18px;
  accent-color: var(--navy);
}
.save .btn-go {
  justify-self: start;
}
.aside {
  margin: 20px 0 0;
  font-size: 14px;
  color: var(--muted);
}
.aside .text-link {
  min-height: 0;
  padding: 0;
  border: 0;
  background: none;
  font: inherit;
}
.error {
  margin: 4px 0 0;
  font-size: 13px;
}
</style>
