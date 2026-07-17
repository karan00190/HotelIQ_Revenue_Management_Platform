# How This Assistant Works

## Tools for data, knowledge search for explanations

This assistant answers questions in two different ways, and it's important they never get mixed up. Questions about real numbers — revenue, occupancy, bookings, forecasts, pricing recommendations — are always answered by calling a tool: a real function that queries the actual database or runs the actual forecasting model, the same code the dashboard and API use. Questions about how the platform works or what a term means — what is RevPAR, how does the pricing engine decide on a price, why doesn't the system claim to predict price elasticity — are answered by searching a small knowledge base of written explanations and are never used to answer questions that need a real figure.

## Why this assistant should never make up a number

If this assistant ever states a specific number — a revenue figure, an occupancy percentage, a forecast — without having called a tool to get it in this same conversation, that is a failure of the design, not an acceptable shortcut. The whole point of building tool-calling into this assistant, rather than just letting a language model answer freely, is that language models are fluent but not reliable at exact figures — they can produce a plausible-sounding number that is simply wrong. Every real number this assistant states should be traceable to a specific tool call, which is why the interface shows which tools were called for each answer.

## What happens when a tool fails or data isn't available

If a tool call fails — for example, a hotel name doesn't match any hotel in the system, or a forecast can't be generated for a requested date — the assistant is instructed to say so plainly rather than guessing or making up a plausible-sounding answer. An honest "I don't have that information" or "that tool returned an error" is always the correct response, never a fabricated substitute.
