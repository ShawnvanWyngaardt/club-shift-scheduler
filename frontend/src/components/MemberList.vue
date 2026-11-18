<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ApiError, coordinatorApi, type Ledger, type MemberLink } from '@/api'
import { useNotice } from '@/composables/useNotice'
import { copyText, memberUrl, whatsappUrl } from '@/links'
import {
  findMembers,
  historyFor,
  memberRows,
  pageOf,
  type MemberRow,
  type MemberSort,
} from '@/members'

const props = defineProps<{ clubId: string; token: string }>()
const emit = defineEmits<{ count: [members: number] }>()
const clubId = computed(() => Number(props.clubId))
const { showNotice } = useNotice()

const links = ref<MemberLink[]>([])
const ledger = ref<Ledger>({ balances: [], entries: [] })
const state = ref<'loading' | 'ready' | 'error'>('loading')

const query = ref('')
const sort = ref<MemberSort>('name')
const page = ref(0)
const open = ref<number | null>(null) // the member whose history is showing
const showAll = ref(false) // their whole season, or the latest few
const revealed = reactive(new Set<number>()) // members whose code is visible
const copied = ref<number | null>(null)
const confirmRemove = ref<number | null>(null)
const rowError = ref<{ id: number; text: string } | null>(null)

const newName = ref('')
const adding = ref(false)
const addError = ref('')

const RECENT = 4

const errorText = (e: unknown) =>
  e instanceof ApiError ? e.message : 'Could not reach the server.'

async function load() {
  state.value = 'loading'
  try {
    const [allLinks, allPoints] = await Promise.all([
      coordinatorApi.memberLinks(clubId.value, props.token),
      coordinatorApi.ledger(clubId.value, props.token),
    ])
    links.value = allLinks
    ledger.value = allPoints
    state.value = 'ready'
  } catch {
    state.value = 'error'
  }
}

const rows = computed(() => memberRows(links.value, ledger.value.balances))
const found = computed(() => findMembers(rows.value, query.value, sort.value))
const shown = computed(() => pageOf(found.value, page.value))
watch([query, sort], () => (page.value = 0)) // a new search starts on page one
watch(
  () => links.value.length,
  (n) => emit('count', n),
)

const history = computed(() =>
  open.value === null ? [] : historyFor(ledger.value.entries, open.value),
)

function toggle(member: MemberRow) {
  open.value = open.value === member.id ? null : member.id
  showAll.value = false
  confirmRemove.value = null
  rowError.value = null
}

function reveal(member: MemberRow) {
  if (revealed.has(member.id)) revealed.delete(member.id)
  else revealed.add(member.id)
}

async function copy(member: MemberRow) {
  copied.value = (await copyText(memberUrl(member.token))) ? member.id : null
}

const shareText = (member: MemberRow) =>
  `Hi ${member.name}, here's your personal link for picking volunteer shifts. ` +
  `It's yours alone, so please don't forward it: ${memberUrl(member.token)}`

async function add() {
  const name = newName.value.trim()
  if (!name) return
  adding.value = true
  addError.value = ''
  try {
    const member = await coordinatorApi.addMember(clubId.value, props.token, name)
    links.value = [...links.value, member]
    newName.value = ''
    showNotice(`${member.name} added.`, 'Send them their link with Copy link or WhatsApp.')
  } catch (e) {
    addError.value = errorText(e)
  } finally {
    adding.value = false
  }
}

async function remove(member: MemberRow) {
  rowError.value = null
  try {
    await coordinatorApi.remove(clubId.value, props.token, 'members', member.id)
    links.value = links.value.filter((l) => l.id !== member.id)
    open.value = null
    showNotice(`${member.name} removed.`, 'Their link no longer works.')
  } catch (e) {
    rowError.value = { id: member.id, text: errorText(e) }
  } finally {
    confirmRemove.value = null
  }
}

const signed = (n: number) => (n > 0 ? `+${n}` : `−${Math.abs(n)}`)
/** A real minus sign, like the history uses, not a hyphen */
const number = (n: number) => (n < 0 ? `−${Math.abs(n)}` : String(n))
const linkBase = `${window.location.host}/m/`

onMounted(load)
</script>

<template>
  <p class="link-base">
    Each member has their own link: <span class="mono">{{ linkBase }}</span>
    <span class="muted">followed by their code</span>
  </p>
  <p class="fair-note">
    The fewest points go first for any shift a member is available for. Members see everyone's
    points in alphabetical order, so it doesn't become a leaderboard. Select a name to see how
    their points add up.
  </p>

  <form class="add" @submit.prevent="add">
    <input
      v-model="newName"
      type="text"
      maxlength="100"
      placeholder="Name of a new member"
      aria-label="Name of a new member"
    />
    <button type="submit" class="btn btn-primary" :disabled="adding || !newName.trim()">
      {{ adding ? 'Adding…' : 'Add member' }}
    </button>
  </form>
  <p v-if="addError" class="error" role="alert">{{ addError }}</p>

  <p v-if="state === 'loading'" class="muted">Loading members…</p>
  <div v-else-if="state === 'error'">
    <p class="error">Couldn't load your members.</p>
    <button type="button" class="btn btn-primary" @click="load">Try again</button>
  </div>
  <p v-else-if="links.length === 0" class="note">
    No members yet. Add the people who help out, then send each one their link.
  </p>

  <template v-else>
    <div class="list-tools">
      <input v-model="query" type="search" placeholder="Find a member" aria-label="Find a member" />
    </div>

    <p v-if="found.length === 0" class="note">Nobody called “{{ query }}”.</p>
    <template v-else>
      <div class="member-cols">
        <button
          type="button"
          class="th-sort"
          :aria-pressed="sort === 'name'"
          @click="sort = 'name'"
        >
          Members{{ sort === 'name' ? ' ↓' : '' }}
        </button>
        <span class="pts">
          <button
            type="button"
            class="th-sort"
            :aria-pressed="sort === 'points'"
            @click="sort = 'points'"
          >
            Points{{ sort === 'points' ? ' ↓' : '' }}
          </button>
        </span>
        <span>Member code</span>
        <span>Actions</span>
      </div>

      <div class="rows">
        <div v-for="m in shown.items" :key="m.id" class="row member-row">
          <span class="name-cell">
            <button
              type="button"
              class="name-btn"
              :aria-expanded="open === m.id"
              :aria-controls="`history-${m.id}`"
              @click="toggle(m)"
            >
              <svg class="chevron" viewBox="0 0 16 16" width="16" height="16" aria-hidden="true">
                <path d="M6 4l4 4-4 4" />
              </svg>
              {{ m.name }}
            </button>
            <span v-if="m.next" class="next-tag">Next</span>
          </span>
          <span class="pts">{{ number(m.points) }}</span>
          <!-- Hidden as dots of the same length, so revealing it doesn't move anything -->
          <span class="code">
            <span class="mono">{{
              revealed.has(m.id) ? m.token : '•'.repeat(m.token.length)
            }}</span>
          </span>
          <div class="btn-row">
            <button
              type="button"
              class="btn btn-small btn-icon"
              :aria-pressed="revealed.has(m.id)"
              :aria-label="`${revealed.has(m.id) ? 'Hide' : 'Show'} ${m.name}'s code`"
              :title="`${revealed.has(m.id) ? 'Hide' : 'Show'} code`"
              @click="reveal(m)"
            >
              <svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true" class="eye">
                <path d="M1.5 8s2.4-4.5 6.5-4.5S14.5 8 14.5 8 12.1 12.5 8 12.5 1.5 8 1.5 8z" />
                <circle cx="8" cy="8" r="2" />
                <path v-if="revealed.has(m.id)" d="M2.5 13.5l11-11" />
              </svg>
            </button>
            <button type="button" class="btn btn-small btn-ghost" @click="copy(m)">
              {{ copied === m.id ? 'Copied' : 'Copy link' }}
            </button>
            <a
              class="btn btn-small btn-whatsapp"
              :href="whatsappUrl(shareText(m))"
              target="_blank"
              rel="noopener"
            >
              WhatsApp<span class="sr-only"> (opens in a new tab)</span>
            </a>
          </div>

          <div v-if="open === m.id" :id="`history-${m.id}`" class="history">
            <template v-if="history.length">
              <h3>{{ showAll ? 'All shifts this season' : 'Most recent shifts' }}</h3>
              <div
                v-for="(h, i) in showAll ? history : history.slice(0, RECENT)"
                :key="i"
                class="h-row"
              >
                <b :class="h.change > 0 ? 'up' : 'down'">{{ signed(h.change) }}</b>
                <span>
                  {{ h.shift }}
                  <small>{{ [h.date, h.outcome].filter(Boolean).join(' | ') }}</small>
                </span>
              </div>
              <button
                v-if="history.length > RECENT"
                type="button"
                class="more-link"
                @click="showAll = !showAll"
              >
                {{
                  showAll
                    ? 'Show only the most recent'
                    : `Show all ${history.length} shifts this season`
                }}
              </button>
            </template>

            <template v-else>
              <p class="note">No points yet. They go first for any shift they're available for.</p>
              <!-- Only someone without history can go: the ledger keeps everyone with points -->
              <div v-if="confirmRemove === m.id" class="confirm">
                <span>Remove {{ m.name }}? Their link stops working.</span>
                <div class="btn-row">
                  <button type="button" class="btn btn-small btn-primary" @click="remove(m)">
                    Remove {{ m.name }}
                  </button>
                  <button
                    type="button"
                    class="btn btn-small btn-ghost"
                    @click="confirmRemove = null"
                  >
                    Keep
                  </button>
                </div>
              </div>
              <button
                v-else
                type="button"
                class="btn btn-small btn-edit remove"
                @click="confirmRemove = m.id"
              >
                Remove from the club
              </button>
            </template>
            <p v-if="rowError?.id === m.id" class="error" role="alert">{{ rowError.text }}</p>
          </div>
        </div>
      </div>

      <div v-if="shown.pages > 1" class="pager">
        <span>{{ shown.from }}–{{ shown.to }} of {{ found.length }}</span>
        <div class="btn-row">
          <button
            type="button"
            class="btn btn-small btn-ghost"
            :disabled="shown.page === 0"
            @click="page = shown.page - 1"
          >
            Previous
          </button>
          <button
            type="button"
            class="btn btn-small btn-ghost"
            :disabled="shown.page >= shown.pages - 1"
            @click="page = shown.page + 1"
          >
            Next
          </button>
        </div>
      </div>
    </template>

    <p class="note">
      Codes are hidden so nobody looking over your shoulder can use them. Copy link and WhatsApp
      still send the full link.
    </p>
  </template>
</template>

<style scoped>
.link-base {
  margin: 0 0 12px;
  font-size: 14px;
}
.mono {
  font-family: var(--font-mono);
  font-size: 13px;
}
.muted {
  color: var(--muted);
}
.fair-note {
  margin: 0 0 16px;
  font-size: 14px;
  color: var(--muted);
}
.note {
  margin: 16px 0 0;
  font-size: 13px;
  color: var(--muted);
}
.error {
  margin: 8px 0 0;
  font-size: 13px;
}

/* Text inputs: same height and corners as the buttons beside them */
.add {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 20px;
}
.add input,
.list-tools input {
  min-height: 40px;
  padding: 0 12px;
  border: 1.5px solid var(--line);
  border-radius: 12px;
  background: var(--surface);
  color: var(--ink);
  font: inherit;
  font-size: 14px;
}
.add input {
  flex: 1;
  min-width: 200px;
}
.list-tools {
  margin-bottom: 12px;
}
.list-tools input {
  min-height: 36px;
  min-width: min(240px, 100%);
}

.rows {
  display: grid;
  gap: 8px;
}
.member-row,
.member-cols {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 90px minmax(0, 1.3fr) 250px;
  align-items: center;
  gap: 16px;
}
.member-row {
  padding: 12px 16px;
  background: var(--surface);
  border-radius: var(--r);
  box-shadow: var(--shadow);
}
.member-cols {
  padding: 0 16px 8px;
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--muted);
}
.th-sort {
  justify-self: start; /* the global button style would centre it */
  text-align: left;
  min-height: 0;
  padding: 0;
  border: 0;
  background: none;
  font: inherit;
  letter-spacing: inherit;
  text-transform: inherit;
  color: var(--navy);
}
.th-sort[aria-pressed='false'] {
  color: var(--muted);
}
.pts {
  display: flex;
  justify-content: center;
  font-variant-numeric: tabular-nums;
}
.member-row .pts {
  font-weight: 600;
}
.name-cell {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}
.name-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 0;
  padding: 0;
  border: 0;
  background: none;
  font: inherit;
  font-weight: 700;
  text-align: left;
  color: var(--ink);
}
.name-btn:hover {
  color: var(--navy);
}
.chevron {
  flex: none;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.75;
  stroke-linecap: round;
  stroke-linejoin: round;
  color: var(--muted);
  transition: transform 200ms ease;
}
.name-btn[aria-expanded='true'] .chevron {
  transform: rotate(90deg);
  color: var(--navy);
}
@media (prefers-reduced-motion: reduce) {
  .chevron {
    transition: none;
  }
}
.next-tag {
  padding: 1px 8px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--sky) 16%, transparent);
  font-size: 11px;
  font-weight: 700;
  color: var(--navy);
}
.code {
  display: flex;
  min-width: 0;
}
.code .mono {
  overflow: hidden;
  font-size: 12px;
  color: var(--muted);
  text-overflow: ellipsis;
  white-space: nowrap;
}
.eye {
  fill: none;
  stroke: currentColor;
  stroke-width: 1.5;
  stroke-linecap: round;
  stroke-linejoin: round;
}

/* Opened row: points history across the full width */
.history {
  grid-column: 1 / -1;
  display: grid;
  gap: 6px;
  padding: 12px 0 4px;
  border-top: 1px solid var(--line);
}
.history h3 {
  margin: 0 0 2px;
  font-size: 12px;
  font-weight: 600;
  color: var(--muted);
}
.history .note {
  margin: 0;
}
.h-row {
  display: flex;
  align-items: baseline;
  gap: 12px;
  font-size: 13px;
}
.h-row b {
  flex: none;
  width: 28px;
  text-align: center;
  font-variant-numeric: tabular-nums;
}
.h-row small {
  display: block;
  font-family: var(--font-time);
  font-size: 11px;
  color: var(--muted);
}
/* Missed stays grey: colour only for what went well */
.h-row .up {
  color: var(--green-ink);
}
.h-row .down {
  color: var(--muted);
}
.more-link {
  justify-self: start;
  min-height: 0;
  padding: 0;
  border: 0;
  background: none;
  font: inherit;
  font-size: 12px;
  font-weight: 600;
  color: var(--navy);
  text-decoration: underline;
}
.remove {
  justify-self: start;
}
.confirm {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 16px;
  font-size: 14px;
}

.pager {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 12px;
  font-size: 13px;
  color: var(--muted);
}

@media (max-width: 900px) {
  .member-cols {
    display: none;
  }
  .member-row {
    grid-template-columns: minmax(0, 1fr) auto;
    gap: 8px 16px;
  }
  .member-row .code,
  .member-row .btn-icon {
    display: none; /* no code column on a phone; the buttons still send the full link */
  }
  .member-row .btn-row {
    grid-column: 1 / -1;
  }
}
</style>
