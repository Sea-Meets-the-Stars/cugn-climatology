# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository generates climatologies for the California Underwater Glider Network (CUGN), which operates Spray underwater gliders along the California coast.

## Working Conventions

- **Git:** The user (not Claude) will perform all git commands (add, commit, push, etc.). Do not run git commands unless explicitly asked.
- **Calculations:** If you do any calculation, generate it as a Python script and write it to disk so that it can be added to the repository. Do not perform one-off calculations only in memory or in the chat.
- **Python environment:** If you need to run Python, use the `ocean14` conda environment.

## Related Repositories

- **cugn:** The main CUGN analysis package lives on this computer at `/home/xavier/Oceanography/python/cugn`. Refer to it for glider data handling, existing analysis code, and project conventions.
