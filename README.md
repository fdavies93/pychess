# PyChess - Simple Python Chess Game

This is a simple console game of chess. It's designed for two purposes:
- As an actual chess game you can play on the terminal
- As a platform for machine learning, evolutionary algorithms, and other AI
experiments

It was inspired by a programming meme involving console based chess.

If you have any pull requests, feel free to file them!

## Design Goals

**Functional:** Use a broadly functional approach to code for increased
flexibility. For example, prefer returning new positions over modifying
existing ones, and keep state such as game history on the highest level
possible.

**Modularity:** Allow easily switching out key modules, especially I/O and
models for AI. This should allow working with both existing chess engines and
with new models.

**DRY:** This is a little challenging in chess, as often we can view similar
operations from different perspectives. E.g. generating all valid moves has
several 'passes' involved.

## TODO
- [ ] Refactor code to be more sensible and succinct while still keeping
broadly functional approach
- [ ] Implement en passant rule
- [ ] Refactor to increase modularity of rendering and input (ie to lay
groundwork for AI / other interface options)
