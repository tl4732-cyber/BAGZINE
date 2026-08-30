import { StoryDeck } from "../components/StoryDeck";

const BRAND_CARDS = [
  {
    title: "The start",
    paragraphs: [
      "BAGZINE was born out of a love for handbags and a curiosity about price tags. Because let's be honest, as much as we care about how a bag looks, it doesn't matter when it's simply not affordable, am I right?",
      "As luxury handbag prices continue to surge, the secondhand market is more appealing than ever. Wonder why?",
    ],
  },
  {
    title: "The Complexity",
    paragraphs: [
      "The appeal goes well beyond price. Shopping secondhand unlocks older versions with superior craftsmanship, rare designs, and discontinued holy grails that haven't graced a boutique in years.",
      "However, finding that bag can feel like detective work. One site has the bag, another has a different price, another has a different condition, and before you know it, you've opened fifteen tabs just trying to figure out what the market actually looks like.",
      "Therefore, BAGZINE is my attempt to make that hunt a little easier.",
    ],
  },
  {
    title: "The Vision",
    paragraphs: [
      "For now, BAGZINE brings together listings from eBay and Fashionphile, giving you a quick snapshot of what your favorite bags are actually selling for across the market. The goal isn't to sell you anything. It's to help you understand the price point before you buy.",
      "And this is only the beginning. As BAGZINE grows, I want to bring in more trusted marketplaces, more brands, more bag models, and more historical price data so that eventually you can look at a bag and understand not just what it costs today, but how that price has evolved.",
    ],
  },
  {
    title: "The evolution",
    paragraphs: [
      "A price can tell you what the market thinks a bag is worth. People can tell you whether it's actually worth it. That's where BAGZINE is heading next.",
      "I'm building tools to listen to the conversations happening around handbags online — what owners love, what they complain about, which bags are suddenly everywhere, which ones are quietly disappearing, and what makes people fall in love with a particular design.",
      "Imagine being able to look at a bag and see: The price. The trend. The sentiment. The conversation. All in one place.",
    ],
  },
  {
    title: "The truth",
    paragraphs: [
      "BAGZINE is also my learning journey. I'm using the project as an opportunity to teach myself how to build a real data engineering system, from collecting and cleaning data, to building databases, analyzing trends, and eventually incorporating AI models.",
      "So the website is evolving alongside me. Some things will work beautifully. Some things will probably break. And some experiments might end up being completely useless. That's part of the fun I believe.",
      "BAGZINE is as much a project about learning how to build with data as it is about handbags!",
    ],
  },
];

export function BrandPage() {
  return <StoryDeck cards={BRAND_CARDS} label="The Brand" />;
}
