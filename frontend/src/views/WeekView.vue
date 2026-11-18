<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import {
  ApiError,
  coordinatorApi,
  type AssignmentDetail,
  type Proposal,
  type ShiftDetail,
} from '@/api'
import AssignmentChange from '@/components/AssignmentChange.vue'
import FillOpenSlot from '@/components/FillOpenSlot.vue'
import { useNotice } from '@/composables/useNotice'
import { points } from '@/format'
import { formatDay, formatTimeRange, weekFromKey } from '@/time'
import { openSlots, shiftCards, type ShiftCard } from '@/week'

const props = defineProps<{ clubId: string; token: string; week: string }>()
const clubId = computed(() => Number(props.clubId))
const { showNotice } = useNotice()

// The week from the URL ("2026-W48"). Generate and Publish only touch this week.
const clubWeek = computed(() => weekFromKey(props.week))
const range = computed(() =>
  clubWeek.value ? { from: clubWeek.value.start, to: clubWeek.value.end } : undefined,
)
const inWeek = (iso: string) =>
  !!clubWeek.value && iso >= clubWeek.value.start && iso < clubWeek.value.end

const shifts = ref<ShiftDetail[]>([])
const assignments = ref<AssignmentDetail[]>([])
const proposal = ref<Proposal | null>(null)
const showPreview = ref(false)
const state = ref<'loading' | 'ready' | 'error'>('loading')
const working = ref<'preview' | 'publish' | null>(null)
const loadError = ref('')
const actionError = ref('')
const editing = ref<number | null>(null) // the shift whose people are being changed

const errorText = (error: unknown) =>
  error instanceof ApiError ? error.message : 'Could not reach the server.'

// Compare moments, not strings: the API and weekOf may write the same time differently.
const isoTime = (iso: string) => new Date(iso).toISOString()

async function load() {
  if (!clubWeek.value) return
  state.value = 'loading'
  try {
    const [allShifts, allAssignments] = await Promise.all([
      coordinatorApi.shifts(clubId.value),
      coordinatorApi.assignments(clubId.value, props.token),
    ])
    shifts.value = allShifts.filter((s) => inWeek(isoTime(s.starts_at)))
    const ids = new Set(shifts.value.map((s) => s.id))
    assignments.value = allAssignments.filter((a) => ids.has(a.shift_id))
    showPreview.value = false
    editing.value = null
    await explainEmptySlots()
    state.value = 'ready'
  } catch (error) {
    loadError.value = errorText(error)
    state.value = 'error'
  }
}

/** Ask the solver what it would do (saves nothing), so empty slots can say why they're empty. */
async function explainEmptySlots() {
  proposal.value = null
  if (openSlots(shiftCards(shifts.value, assignments.value, null, false)) === 0) return
  try {
    proposal.value = await coordinatorApi.generate(clubId.value, props.token, range.value)
  } catch {
    // Only the reasons are missing; the page still works.
  }
}

async function preview() {
  working.value = 'preview'
  actionError.value = ''
  try {
    proposal.value = await coordinatorApi.generate(clubId.value, props.token, range.value)
    showPreview.value = true
  } catch (error) {
    actionError.value = errorText(error)
  } finally {
    working.value = null
  }
}

async function publish() {
  working.value = 'publish'
  actionError.value = ''
  const wasPublished = published.value
  try {
    const result = await coordinatorApi.publish(clubId.value, props.token, range.value)
    await load()
    const added = result.assignments.length
    showNotice(
      wasPublished
        ? `${added} ${added === 1 ? 'person' : 'people'} added to week ${clubWeek.value?.number}.`
        : `Week ${clubWeek.value?.number} published.`,
      'Members see their shifts on their My shifts page.',
    )
  } catch (error) {
    actionError.value = errorText(error)
  } finally {
    working.value = null
  }
}

const cards = computed(() =>
  shiftCards(shifts.value, assignments.value, proposal.value, showPreview.value),
)
const days = computed(() => {
  const groups = new Map<string, ShiftCard[]>()
  for (const card of cards.value) {
    const day = formatDay(card.shift.starts_at)
    groups.set(day, [...(groups.get(day) ?? []), card])
  }
  return [...groups].map(([day, list]) => ({ day, cards: list }))
})

const published = computed(() => assignments.value.length > 0)
const slots = computed(() => shifts.value.reduce((sum, s) => sum + s.slots, 0))
const filled = computed(() =>
  cards.value.reduce((sum, c) => sum + Math.min(c.holders.length, c.shift.slots), 0),
)
const open = computed(() =>
  openSlots(shiftCards(shifts.value, assignments.value, proposal.value, false)),
)
const adding = computed(() => (showPreview.value ? (proposal.value?.assignments.length ?? 0) : 0))
const stayEmpty = computed(() => openSlots(cards.value))

const changeable = (card: ShiftCard) =>
  !card.started && card.holders.some((h) => h.status === 'assigned')

onMounted(load)
</script>

<template>
  <main class="wrap">
    <RouterLink class="back" :to="{ name: 'overview', params: { clubId, token } }">
      ← Back to Overview
    </RouterLink>

    <section v-if="!clubWeek">
      <h1>This week doesn't exist</h1>
      <p class="muted">Pick a week from the Overview.</p>
    </section>

    <p v-else-if="state === 'loading'" class="muted">Loading week {{ clubWeek?.number }}…</p>

    <section v-else-if="state === 'error'">
      <h1>Couldn't load week {{ clubWeek?.number }}</h1>
      <p class="muted">{{ loadError }}</p>
      <button type="button" class="btn btn-primary" @click="load">Try again</button>
    </section>

    <template v-else>
      <div class="page-head">
        <div>
          <h1>
            Week {{ clubWeek?.number }} <span class="head-dates">{{ clubWeek?.dates }}</span>
          </h1>
          <p v-if="shifts.length">{{ filled }} of {{ slots }} slots filled</p>
        </div>
        <div class="btn-row">
          <template v-if="showPreview">
            <button
              type="button"
              class="btn btn-ghost"
              :disabled="!!working"
              @click="showPreview = false"
            >
              Discard preview
            </button>
            <button
              type="button"
              class="btn btn-go"
              :disabled="!!working || adding === 0"
              @click="publish"
            >
              {{ working === 'publish' ? 'Publishing…' : `Publish week ${clubWeek?.number}` }}
            </button>
          </template>
          <button
            v-else-if="open > 0"
            type="button"
            class="btn btn-go"
            :disabled="!!working"
            @click="preview"
          >
            <template v-if="working === 'preview'">Working it out…</template>
            <template v-else>{{ published ? 'Fill empty slots' : 'Generate preview' }}</template>
          </button>
        </div>
      </div>

      <p v-if="actionError" class="error" role="alert">{{ actionError }}</p>

      <div v-if="showPreview" class="banner" aria-live="polite">
        <span class="pill new">Preview</span>
        <span v-if="adding === 0">
          Nobody available can be added, so there is nothing to publish. Assign someone by hand or
          ask the group.
        </span>
        <span v-else>
          Nothing is saved yet. People marked <b>new</b> are added when you publish.
          {{
            stayEmpty
              ? `${stayEmpty} ${stayEmpty === 1 ? 'slot stays' : 'slots stay'} empty.`
              : 'Every slot is filled.'
          }}
        </span>
      </div>
      <div v-else-if="published" class="banner ok">
        <span class="pill published">Published</span>
        <span>Members see these shifts on their My shifts page.</span>
      </div>

      <p v-if="shifts.length === 0" class="muted">
        No shifts this week.
        <RouterLink class="text-link" :to="{ name: 'setup', params: { clubId, token } }"
          >Add shifts</RouterLink
        >
        to plan it.
      </p>

      <section v-for="group in days" :key="group.day" class="day">
        <h2 class="day-title">{{ group.day }}</h2>
        <div class="shift-grid">
          <article
            v-for="card in group.cards"
            :key="card.shift.id"
            class="shift"
            :class="{ 'has-gap': card.emptySlots.length > 0, started: card.started }"
          >
            <div class="shift-top">
              <div>
                <div class="shift-name">{{ card.shift.shift_type }}</div>
                <div class="shift-time">
                  {{ formatTimeRange(card.shift.starts_at, card.shift.ends_at) }}
                </div>
              </div>
              <span class="shift-pts">
                +{{ points(card.shift.weight, { short: true }) }} |
                {{ card.holders.length + card.added.length }}/{{ card.shift.slots }}
              </span>
            </div>

            <div class="slots">
              <span v-for="h in card.holders" :key="h.id" class="chip">{{ h.member_name }}</span>
              <span v-for="name in card.added" :key="`new-${name}`" class="chip is-new">
                {{ name }}
              </span>
              <div v-for="(reason, i) in card.emptySlots" :key="i" class="empty-slot">
                <span><b>{{ reason.title }}</b>{{ reason.text }}</span>
                <FillOpenSlot
                  v-if="!card.started && !showPreview"
                  :club-id="clubId"
                  :token="token"
                  :shift-id="card.shift.id"
                  :shift-label="card.shift.shift_type"
                  @changed="load"
                />
              </div>
            </div>

            <p v-if="card.started" class="started-note">Started, so it can't be changed here.</p>
            <template v-else-if="changeable(card) && !showPreview">
              <button
                type="button"
                class="btn btn-small btn-edit change-toggle"
                :aria-expanded="editing === card.shift.id"
                @click="editing = editing === card.shift.id ? null : card.shift.id"
              >
                {{ editing === card.shift.id ? 'Done changing' : 'Change people' }}
              </button>
              <ul v-if="editing === card.shift.id" class="holders">
                <li v-for="h in card.holders.filter((x) => x.status === 'assigned')" :key="h.id">
                  <strong>{{ h.member_name }}</strong>
                  <AssignmentChange :token="token" :assignment="h" @changed="load" />
                </li>
              </ul>
            </template>
          </article>
        </div>
      </section>
    </template>
  </main>
</template>

<style scoped>
.back {
  display: inline-block;
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 600;
  color: var(--navy);
  text-decoration: none;
}
.head-dates {
  font-family: var(--font-time);
  font-size: 16px;
  font-weight: 500;
  color: var(--muted);
}
.error {
  margin: 0 0 16px;
}

.banner {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
  padding: 12px 16px;
  border-radius: var(--r);
  background: color-mix(in srgb, var(--sky) 12%, var(--surface));
  font-size: 14px;
}
.banner.ok {
  background: var(--mint-surface);
}
.pill.new {
  background: var(--sky);
  color: #fff;
}

.day {
  margin-bottom: 28px;
}
.day-title {
  margin: 0 0 10px;
  font-size: 14px;
  font-weight: 600;
}
.shift-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 12px;
}
.shift {
  display: grid;
  align-content: start;
  gap: 10px;
  padding: 14px 16px;
  background: var(--surface);
  border-radius: var(--r);
  border-right: 3px solid var(--green);
  box-shadow: var(--shadow);
}
.shift.has-gap {
  border-right-color: var(--sky);
}
.shift.started {
  opacity: 0.75;
}
.shift-top {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}
.shift-name {
  font-weight: 600;
}
.shift-time {
  font-family: var(--font-time);
  font-size: 13px;
  color: var(--muted);
}
.shift-pts {
  font-size: 12px;
  font-weight: 600;
  white-space: nowrap;
  color: var(--navy);
}
.slots {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  gap: 6px;
}
.chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 999px;
  background: var(--chip);
  font-size: 13px;
  font-weight: 500;
}
.chip.is-new {
  background: color-mix(in srgb, var(--sky) 18%, var(--surface));
  box-shadow: inset 0 0 0 1.5px var(--sky);
}
.chip.is-new::after {
  content: 'new';
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--sky);
}
/* Empty slots are blue: something to fill, not an error */
.empty-slot {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  width: 100%;
  padding: 8px 10px;
  border-radius: var(--r);
  border: 1.5px dashed var(--sky);
  background: color-mix(in srgb, var(--sky) 10%, transparent);
}
.empty-slot > span {
  font-size: 13px;
  color: var(--navy);
}
.empty-slot b {
  display: block;
}
.started-note {
  margin: 0;
  font-size: 13px;
  color: var(--muted);
}
.change-toggle {
  justify-self: start;
}
.holders {
  display: grid;
  gap: 10px;
  margin: 0;
  padding: 0;
  list-style: none;
}
.holders strong {
  font-size: 14px;
}
</style>
