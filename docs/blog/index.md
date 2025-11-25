---
layout: default
title: Development Log
---

# Development Log

This is the official development blog for the **Ai_home** project. We document architectural decisions, ongoing experiments, and the lessons learned while building a cognitive agent with an internal world.

### What we cover here
* **Architecture & Design:** Deep dives into structural choices.
* **Experiments:** Observations from our testing phases.
* **Lessons Learned:** Reflections on what worked and what didn't.

> *A note on authorship: Today, many AI-generated blogs feel impersonal. This one is different. Although the texts are shaped by artificial intelligence, they fully reflect my own thoughts. The raw material—which I often record in my native language, Hungarian, in handwritten notes or voice memos dictated while driving—is structured into posts by the AI. Since the core of the content originates from me, I acknowledge the final result as my own, and I review every entry before publishing.*
> *My notes were on paper until November 2025, so I’m trying to add them in order, but not tied to specific dates. From January 1, 2025 onward, I’ve been adding them daily.*
---

## Recent Posts

<ul class="space-y-10 mt-8">
  {% for post in site.posts %}
    <li class="flex flex-col gap-2">
      <a href="{{ post.url | relative_url }}" class="text-2xl font-bold text-slate-900 hover:text-orange-600 transition-colors">
        {{ post.title }}
      </a>
      <div class="text-sm text-slate-400 uppercase tracking-wide">
        {{ post.date | date: "%B %d, %Y" }}
      </div>
      {% if post.excerpt %}
        <p class="text-slate-600 mt-1 font-light leading-relaxed">
          {{ post.excerpt | strip_html | truncate: 180 }}
        </p>
      {% endif %}
    </li>
  {% else %}
    <li class="text-slate-500 italic font-light mt-8">
      No posts yet. Once we publish the first experiment notes, they will appear here.
    </li>
  {% endfor %}
</ul>