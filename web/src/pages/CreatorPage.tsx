import { StoryDeck } from "../components/StoryDeck";

const CREATOR_CARDS = [
  {
    title: "The background",
    paragraphs: [
      "My name is Lucy, and I'm a Computer Science graduate student at New York University. Before computer science, I worked in data analytics across fintech and adtech, where I spent my days turning messy data into insights, building reporting systems, and working with engineers to solve problems at scale.",
      "Somewhere along the way, I realized I was becoming increasingly curious about what happened before the analysis. How does the data get there? What moves it from one system to another? What makes a pipeline reliable? And what actually happens behind the scenes to turn raw data into the ready-to-use dashboards businesses rely on?",
      "That curiosity eventually led me toward engineering.",
    ],
  },
  {
    title: "The experiences",
    paragraphs: [
      "At a fintech company, I worked as a Data Engineer Intern, where I built end-to-end ETL pipelines, transforming raw financial data into downstream Excel reports efficiently. I also worked on pipeline infrastructure, data quality checks, database schemas, and a transaction monitoring system designed to process data at scale.",
      "Previously, in adtech, I helped execute the migration of more than 2 million records to Google Cloud, collaborated with engineers on AI-powered advertising products, and built Python-based analysis tools that turned large amounts of behavioral data into actionable insights, supporting decision-making and revenue growth.",
      "These experiences taught me how powerful data can be. They also made me want to be the one building the machinery behind it.",
    ],
  },
  {
    title: "The projects",
    paragraphs: [
      "On top of my professional experience, I've been applying what I learn through hands-on projects. There's a full-stack messaging application I built with a teammate using Django REST Framework, PostgreSQL, scalable REST APIs, and modular backend services.",
      "There's also a data science project where, as a team of 3, we applied Bayesian logistic regression to investigate the relationship between marital status and income, uncovering some interesting patterns along the way.",
      "And then there's this. BAGZINE. A project that combines something I've always loved(bags) with something I've unexpectedly grown to love(engineering).",
      <>
        You can find more of my projects and code on my{" "}
        <a
          href="https://github.com/tl4732-cyber"
          target="_blank"
          rel="noreferrer"
          onClick={(event) => event.stopPropagation()}
        >
          GitHub
        </a>
        .
      </>,
    ],
  },
  {
    title: "The history",
    paragraphs: [
      "The root was always there. I just didn't know it.",
      "My dad used to be an engineer. My brother has become an engineer. Growing up, I listened to them talk about engineering, technology, robots, and all sorts of things I found profoundly uninteresting.",
      "I loved reading fashion magazines. I thought maybe I'd work in publishing someday. As it turned out, I got a degree in journalism, and my first job after school took me to the intersection of media and technology.",
      "Somewhere along the way, I unexpectedly discovered that I loved working with data and technology. And somehow, I ended up following the family after all. Life really is interesting and full of surprises sometimes!",
    ],
  },
  {
    title: "The future",
    paragraphs: [
      "Today, I'm actively looking for opportunities in data and software engineering, where I can continue to grow as an engineer, build reliable systems, and solve meaningful problems at scale.",
      "I'm particularly interested in opportunities where I can combine my background in data with strong technical foundations to build systems that don't just work, but make people's work better and easier.",
      "If you'd like to learn more about me, see my resume, collaborate, or even suggest something you'd like to see BAGZINE build next, please don't hesitate to reach out.",
      "I genuinely welcome and truly appreciate any advice along the way :)",
    ],
  },
];

export function CreatorPage() {
  return <StoryDeck cards={CREATOR_CARDS} label="The Creator" />;
}
