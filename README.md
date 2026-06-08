# Gothic Lock Solver

A small web app for solving lockpicking puzzles in **Gothic Remake**.

The app takes the current lock positions and dependencies between locks, then finds a valid sequence of moves using a shortest-path search.

## Versions

There are two versions of the app:

### Original version

https://gothiclocksolver.streamlit.app/

In the original version, you have to pass through seven warning gates before getting access to the solver.

This version is meant for players who want an external safeguard against giving up on the challenge too quickly. The gates are intentionally annoying and are there to give you a few extra chances to stop, go back to the game, and try solving the lock yourself.

### Direct version

https://gothiclocksolverdirect.streamlit.app/

The direct version gives immediate access to the solver.

This version is meant for players who already know they want help and do not want to go through the warning flow.

## Intended use

This app was made mainly with console players in mind, since they do not have the same access to mods as PC players. It may also be useful for players who are completely stuck and would otherwise look for a ready-made solution online anyway.

I still encourage you to use the app only as a last resort, in a final act of frustration or desperation. The lockpicking system is part of the challenge prepared by the developers, and overusing a solver can easily make the game less interesting.

## How it works

The app uses breadth-first search (BFS) to find the shortest valid sequence of moves from the current lock configuration to the target state.

In the game, clicking left and right can move locks in unintuitive ways, and some locks may affect other locks. The solver represents each configuration as a state and searches for a valid path to the solved state.

## Development plans

I plan to add Polish and German language versions of the app.

If you have suggestions for improving the app, the interface, the wording, or the solver itself, feel free to let me know.

## Notes

The app is free, has no ads, no paid features, and does not collect user data.

The code is open so anyone can inspect it, modify it, or run their own version.

## Other options

The main feature of this app is the self-check flow before deciding to make the game easier. If you only want direct access to a solver, there are already plenty of other lock-solving apps created by the community. Here is a list of the ones I found: 

https://xetoxyc.github.io/gothic-remake-lockpicker/ 
https://github.com/kamilcieslik/gothic-remake-lockbreaker 
https://nutschulk.github.io/GothicRemakeChestSolver/index.html

