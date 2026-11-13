<script setup lang="ts">
import wave from "@/assets/landing/how-it-works-wave.svg";
import stepTick from "@/assets/landing/step-1-tick.png";
import stepShare from "@/assets/landing/step-2-share.png";
import stepPoints from "@/assets/landing/step-3-points.png";

const steps = [
  {
    title: "Tick what you can do",
    text: "Everyone gets a personal link. No account, no app to install.",
    image: stepTick,
    alt: "Two shifts with points: Bar, early Saturday unticked, Field setup ticked.",
  },
  {
    title: "Share it out in one click",
    text: "The fewest points go first, and any gaps show up straight away.",
    image: stepShare,
    alt: "Youth referee, 3 of 3 filled: Emma and Daan newly added, Noa already on it.",
  },
  {
    title: "Fair next time too",
    text:
      "Every shift done earns points. The less popular the shift, the more it's worth.",
    image: stepPoints,
    alt: "Points per member: Daan 1, Emma 3, Noa 4.",
  },
];
</script>

<template>
  <section id="how" class="how" aria-labelledby="how-title">
    <div class="art">
      <!-- Decorative: the wave across the top and the stripes down the left. -->
      <img class="wave" :src="wave" alt="" width="1101" height="159" />
      <div class="stripes" aria-hidden="true"></div>

      <div class="panel">
        <p class="real-club">
          Running a real club?
          <RouterLink to="/start">Start your own club*</RouterLink>
        </p>
        <p class="beta">* currently in beta</p>

        <p class="eyebrow">How it works</p>
        <h2 id="how-title" class="text-light">One round, three steps</h2>

        <ol class="steps">
          <li v-for="(step, index) in steps" :key="step.title" class="step">
            <span class="num" aria-hidden="true">{{ index + 1 }}</span>
            <h3>{{ step.title }}</h3>
            <p>{{ step.text }}</p>
            <img :src="step.image" :alt="step.alt" class="step-img" loading="lazy" />
          </li>
        </ol>
      </div>
    </div>
  </section>
</template>

<style scoped>
/* Values from the Figma frame "How it works" (node 297:580, 1440 wide). */
.how {
  --how-bg: #f8f5fb;
  --how-plum: #210124;
  --how-blue: #084887;
  --how-orange: #f34213;
  --how-amber: #f58a07;
  --how-eyebrow: #f0531c;
  --how-ink: #22102a;
  --how-muted: #6b5d73;
  --how-light: #f7f5fb;

  background: var(--how-bg);
  overflow: hidden;
}

/*
 * The artwork is 1101 wide in the design. It's a size container, so the wave,
 * the stripes and the panel's offsets scale together at every width (cqw = 1% of it).
 */
.art {
  container-type: inline-size;
  position: relative;
  width: min(1101px, 100%);
  margin-left: max(0px, calc(50% - 537px)); /* x 183 at 1440, as in the design */
}
.wave {
  position: absolute;
  inset: 0 0 auto 0;
  z-index: 2;
  display: block;
  width: 100%;
  height: auto;
  pointer-events: none; /* decorative: never block clicks on what's underneath */
}
.stripes {
  position: absolute;
  left: 0;
  top: 14.35cqw; /* 158 of 1101: where the wave ends */
  bottom: 0;
  width: 6.54cqw; /* 72 of 1101 */
  background: linear-gradient(
    90deg,
    var(--how-amber) 0 15.28%,
    var(--how-orange) 15.28% 36.11%,
    var(--how-blue) 36.11% 65.28%,
    var(--how-plum) 65.28% 100%
  );
}
.panel {
  /* No z-index here: it would trap .real-club's z-index below the wave */
  position: relative;
  margin-left: 6.54cqw;
  margin-top: 5.63cqw; /* 62 of 1101 */
  padding: 64px 20px 99px;
  background: linear-gradient(90deg, var(--how-plum) 33.17%, var(--how-blue));
  color: #fff;
}

.real-club {
  position: relative;
  z-index: 3; /* above the wave where they overlap on narrow screens */
  font-size: 16px;
  color: var(--how-light);
  margin: 0;
}
.real-club a {
  font-weight: 600;
  color: var(--how-amber);
  text-decoration: underline;
  text-underline-position: from-font;
}
.real-club a:focus-visible {
  outline: 3px solid var(--how-amber);
  outline-offset: 3px;
}
.beta {
  font-size: 10px;
  font-style: italic;
  color: rgba(247, 245, 251, 0.75);
  margin: 9px 0 0;
}

.eyebrow {
  font-family: var(--font-mono);
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.06em; /* 0.78px */
  text-transform: uppercase;
  color: var(--how-eyebrow);
  margin: 72px 0 0;
}
h2 {
  color: var(--color-text-light);
  font-size: 32px;
  line-height: 46px;
  font-weight: 800;
  letter-spacing: -0.025em; /* -0.8px */
  margin: 10px 0 0;
}

.steps {
  list-style: none;
  display: grid;
  grid-template-columns: 1fr;
  gap: 36px;
  margin: 40px 0 0;
  padding: 0;
}
.step {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-height: 290px;
  padding: 22px;
  border-radius: 20px;
  background: #fff;
  color: var(--how-ink);
  filter: drop-shadow(0 12px 15px rgba(60, 20, 70, 0.35));
}
.num {
  position: absolute;
  top: -15px;
  left: 23px;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: var(--how-orange);
  color: #fff;
  font-size: 14px;
  font-weight: 800;
}
.step h3 {
  font-size: 19px;
  font-weight: 700;
  letter-spacing: -0.01em;
  margin: 0;
}
.step p {
  font-size: 15px;
  line-height: 22.5px;
  color: var(--how-muted);
  margin: 0;
  max-width: 236px;
}
.step-img {
  display: block;
  width: 236px;
  max-width: 100%;
  height: auto;
  margin-top: auto; /* the three pictures line up along the bottom of the cards */
}

/* Desktop: as in the Figma frame */
@media (min-width: 960px) {
  .panel {
    padding: 64px 0 99px 55px;
  }
  .real-club,
  .beta,
  .eyebrow,
  h2 {
    margin-left: 23px; /* the text lines up with the content inside the cards */
  }
  .steps {
    grid-template-columns: repeat(3, 285px);
    gap: 36px;
  }
}
</style>
