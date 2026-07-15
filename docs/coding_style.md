## Rules:

 - always use `black` formatting, even if it's doing weird things
 - Keep It Stupid Simple
    - Do not abstract for imaginary requirements, only for current requirement unless we have written plans.
    - code should be readable, comment only on weird external behavior
    - Things that rarelly gets used do not need to be polished, eg: bot onboarding
 - use Python features and included/system libaries as much as possible
    - eg: `match()` instead of cascade of `if: else:`
    - 3rd party libaries need to have a purpuse to be added

## Logging:

 - debug: it's ok to use often as it's only logged to file, if high frequency put behind a feature flag
 - info : logged to discord, do not abuse, only important information.
 - warning : use when a degraded path is being used or error on user side
 - error/exception: your code should be perfect

## Architecture:

The bot is seperated in layers:
- `business`: most of the logic is handled here, it was initially supposed to be decoupled from discord to allow alternatives.
- `storage`: interaction with database
- `ui`: discord integration code (commands declaration and some logic), web server (deprecated, lack of ressource and interest)

This segmentation would have allowed to use a test suite to run the business logic. sadly due to lack of ressource the test suite was working way after the bot put in production. this imply that some logic was implemented in the ui layer and is there for not aable to be tested by scripts

## Test Suite:

It is relativelly new compare to the codebase of the bot.

Rules:
 - only add test case for new system, or high risk systems (inactive purge)
 - TBA