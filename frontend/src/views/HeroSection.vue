<script setup lang="ts">
import { useStartDemo } from "@/composables/useStartDemo";
import heroPhone from "@/assets/landing/hero-phone-poster.webp";

const { phase, isBusy, startDemo } = useStartDemo();
</script>

<template>
  <section class="hero" aria-labelledby="hero-title">
    <div class="hero-inner">
      <div class="hero-text">
        <p class="kicker">Volunteer shifts for sports clubs</p>
        <h1 id="hero-title">Fair shifts, without the group chat.</h1>
        <p class="sub">
          Members tick the shifts they can do. The app shares them out fairly, and whoever
          has done the least goes first.
        </p>

        <button type="button" class="cta" :disabled="isBusy()" @click="startDemo">
          {{ isBusy() ? "Setting up your demo…" : "Try the demo" }}
        </button>

        <p class="status" aria-live="polite">
          <template v-if="phase === 'waking'">
            Waking up the server. On the first visit this can take up to a minute; your
            demo opens by itself.
          </template>
          <template v-else-if="phase === 'full'">
            A lot of people are trying the demo right now. Please try again in a few
            minutes.
          </template>
          <template v-else-if="phase === 'failed'">
            We couldn't reach the server. Check your connection and try again.
          </template>
          <template v-else
            >A private sample club, ready in seconds. <b>No sign-up.</b></template
          >
        </p>
      </div>

      <figure class="hero-img">
        <img
          :src="heroPhone"
          width="1000"
          height="1200"
          alt="A member's availability screen on a phone: Saturday shifts, one ticked, each showing the points it earns."
        />
      </figure>
    </div>
  </section>
</template>

<style scoped>
/* Values from the Figma frame "HERO" (node 295:540, 1440 wide). */
.hero {
  --hero-bg: #f8f5fb;
  --hero-ink: #210124;
  --hero-muted: #6b5d73;
  --hero-strong: #22102a;
  --hero-orange: #f34213;
  --hero-ember: #ff7a18;
  --hero-amber: #f58a07;
  --font-display: "Titan One", system-ui, sans-serif;

  background: var(--hero-bg);
  color: var(--hero-ink);
  padding: 48px 20px 56px;
}
.hero-inner {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.kicker {
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.065em; /* 0.78px at 12px */
  text-transform: uppercase;
  color: var(--hero-orange);
  margin: 0 0 12px;
}
h1 {
  font-family: var(--font-display);
  font-size: 40px;
  line-height: 1.08;
  letter-spacing: -0.03em;
  font-weight: 400; /* Titan One has a single weight; 700 would make the browser fake a bold */
  margin: 0 0 20px;
}
.sub {
  font-size: 16px;
  line-height: 24px;
  color: var(--hero-muted);
  margin: 0 0 38px;
  max-width: 306px;
}

.cta {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 44px;
  padding: 10px 24px;
  border: 1px solid rgba(255, 255, 255, 0.38);
  border-radius: 16px;
  font: inherit;
  font-size: 16px;
  line-height: 24px;
  font-weight: 800;
  color: #fff;
  background: linear-gradient(
    90deg,
    var(--hero-orange) 17.3%,
    var(--hero-ember) 81.25%,
    var(--hero-amber) 92.3%
  );
  cursor: pointer;
}
.cta:hover {
  filter: brightness(1.05);
}
.cta:focus-visible {
  outline: 3px solid var(--hero-ink);
  outline-offset: 3px;
}
.cta:disabled {
  cursor: progress;
  opacity: 0.8;
}

.status {
  font-size: 12px;
  line-height: 1.25;
  color: var(--hero-muted);
  margin: 18px 0 0;
  min-height: 30px; /* room for the waiting message, so nothing below jumps */
  max-width: 316px;
}
.status b {
  color: var(--hero-strong);
}

.hero-img {
  margin: 0;
  align-self: center;
}
.hero-img img {
  display: block;
  width: min(300px, 78vw);
  height: auto;
}

/* Desktop: two columns, as in the Figma frame */
@media (min-width: 960px) {
  .hero {
    padding: 100px 40px 64px;
  }
  .hero-inner {
    display: grid;
    grid-template-columns: 434px 359px;
    column-gap: 32px;
    align-items: start;
    /* At 1440 wide this puts the text at x 330, as in the design. */
    margin-left: max(0px, calc(50% - 390px));
  }
  h1 {
    font-size: 60px;
    line-height: 64.8px;
  }
  .cta {
    width: 360px;
  }
  .hero-img {
    margin-top: -16px; /* the image starts 16px above the kicker */
  }
  .hero-img img {
    width: 359px;
  }
}

@media (prefers-reduced-motion: no-preference) {
  .cta {
    transition: filter 0.15s ease;
  }
}
</style>
