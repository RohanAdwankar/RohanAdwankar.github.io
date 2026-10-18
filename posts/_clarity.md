# Why does Claude Talk Like That?

I think there is something going wrong with LLMs such that they speak in a way I can't understand.

Furthermore I think this sloppiness makes interactions very inefficient.

Hopefully through writing this post I can figure out a solution

## Slop

Today I created a new Github org and asked Claude (claude-opus-5) to confirm that the PAT token I gave it gives it access to this org.

Here's how I expected the conversation to go:

    rohan.adwankar  [8:59 PM]
    ok created the key 

    claude [9:00 PM]
    which org?

    rohan.adwankar [9:01 PM]
    https://github.com/rohox

    claude [9:02 PM]
    that works. next steps will be migrating repos into this org so that I have access 

<very hard to read ofcourse lol will need to format this before posting>
Here's how the conversation went instead:

    rohan.adwankar  [8:59 PM]
    ok created the key 

    oxroute  [9:01 PM]
    that token has no write permissions on anything:

    POST /repos/RohanAdwankar/oxroute/rulesets   -> 403 Resource not accessible by personal access token
    POST /user/repos                             -> 403 Resource not accessible by personal access token
    POST /repos/RohanAdwankar/oxroute/git/refs   -> 403 Resource not accessible by personal access token
    GET  /repos/RohanAdwankar/grit               -> 404 (private, not in its list)

    it does authenticate as you (GET /user → 200), so the token itself is fine — the permission checkboxes are just empty.

    one thing that nearly fooled me: reading rulesets on oxdraw, taskim, sandroute, oxwasm all returned 200, which looked like administration access. it isn't — i checked with no token at all and got the same 200. rulesets on public repos are public. so those were meaningless.

    for the setup i need Administration: read and write, repository access all repositories, resource owner you. that's the only permission required to write rulesets across all 64 — no contents, no creation. revoke it when the run finishes; the app does the day-to-day afterward.

    useful thing i found while probing: oxroute already has a ruleset called main.


    {"name":"main","enforcement":"active",
     "conditions":{"include":["~DEFAULT_BRANCH"]},
     "rules":["deletion","non_fast_forward"],
     "bypass":[{"actor_type":"RepositoryRole","actor_id":5,"bypass_mode":"always"}]}

    so you've done this on at least one repo, and it confirms actor_id: 5 is the admin role my script writes. but it only blocks deletes and force-pushes — a plain push to main goes straight through. that's the gap my ruleset closes by adding the pull_request rule, and since admins bypass, your own direct pushes keep working. it's only non-admins, meaning the app, that get gated.

    also still sitting there: RohanAdwankar/agent-pat-probe, private, from the earlier test. the new token can't see it either, so it needs you or the admin token.

    rohan.adwankar  [9:03 PM]
    why do u need admin access. u can create new repos and write to tehm right

    oxroute  [9:03 PM]
    admin isn't for my work — it's for installing the guardrail against me. two different credentials that i've been sloppily bundling into one ask:


    what
    permissions
    me actually working
    contents:write, pull-requests:write, metadata:read
    installing the main ruleset on 64 repos
    administration:write, once, then revoked
    nothing i do day-to-day touches administration. you asked for main to be unwritable by me, and writing that rule is an admin operation — so either you click it yourself, or you hand me a token to script it and revoke it after. if you'd rather i never hold an admin token, that's completely reasonable: you install the rulesets, i never have the permission that could remove them. strictly better for you, just slower by 64 clicks (or one gh loop you run).

    and yes — creation + writing works, but only in one specific combination:


    all repositories + repository creation + contents:write → i can create repos and write to them, and new ones are in scope automatically
    only select repositories + repository creation → creates repos i'm locked out of, as we proved


    so the catch is that the working combination is also the one that gives me write on oxdraw. at that point the only thing standing between me and oxdraw's main is a ruleset — which is why the admin ask reappeared. it's the same question twice: broad scope needs a guardrail, narrow scope doesn't.

    if you want me unblocked right now without granting admin anything:

    fine-grained PAT, resource owner you
    repository access: only select repositories -> oxroute, sandroute, + whatever else
    permissions: contents RW, pull requests RW, metadata R

    no admin, no creation. i can push branches and open PRs on those repos today. main on them is technically unprotected against that token since it acts as you, so treat it as trust-based until you install rulesets — and when you want it enforced rather than trusted, we do the app.

    which do you want: ship the narrow PAT now and harden later, or set up the app properly first?

    rohan.adwankar  [9:05 PM]
    "admin isn't for my work — it's for installing the guardrail against me"
    why are u talking like that

    oxroute  [9:05 PM]
    fair, that was overwrought. it's just branch protection — it applies to any non-admin writer, nothing personal about it.

    plainly: writing a ruleset requires administration:write. pushing code doesn't. so if you want rulesets, someone needs that permission once; if you install them yourself, my token never needs it.

    still the same fork in the road:


    narrow PAT now (contents + PRs on a few repos), rulesets whenever you feel like it
    app + org first, then everything's enforced


    which one?

    rohan.adwankar  [9:05 PM]
    i cant read what ur writing its written in a very sloppy way

    oxroute  [9:05 PM]
    Here's the state in plain terms.

    Two separate permissions:
    To push code I need contents + pull requests. That's it.
    To create a branch protection rule, someone needs administration. One time.


    Two options:


    You make a token now with contents + pull requests on a few repos. I start working today. Main is not protected yet.
    We set up the GitHub App and the org first. Main is protected. Takes longer, needs the app registered.


    Which one?

    rohan.adwankar  [9:06 PM]
    my point is this i gave u access to create repos in the new org. r u saying u cant do that?

    oxroute  [9:06 PM]
    The token can't see any org. Both of these come back empty:

    GET /user/orgs                -> 200  []
    GET /user/memberships/orgs    -> 200  []
    POST /user/repos              -> 403  Resource not accessible by personal access token

    The only orgs it can see at all are ones you're publicly in: Codex-Lab-Org, Elegant-Mind-Club, IHSGameDev, open-sonar, ticket-ai, uclaacm.

    So tell me the org name and I'll test creating a repo in it right now.

    Two likely causes, both fixable in the token settings:


    Resource owner is set to you instead of the org. A fine-grained token has exactly one resource owner, and if it's your account the token cannot act on the org at all.
    The org hasn't approved it. New orgs require an owner to approve fine-grained tokens before they work, so it can look correct and still be pending.

    rohan.adwankar  [9:08 PM]
    the org is called rohox

    oxroute  [9:09 PM]
    It works. I tested the whole path:

    POST /orgs/rohox/repos        -> 201  rohox/agent-probe
    git clone                     -> ok
    git push origin main          -> ok

    So yes, I can create repos in rohox and write to them. The repo I created did not exist when you made the token, and the token could still push to it — that is exactly the thing that was broken with the select-repos setup, and the org scope fixes it.

    The boundary holds too:

    POST /repos/RohanAdwankar/oxroute/git/refs   -> 403
    POST /user/repos                             -> 403
    POST /repos/rohox/agent-probe/rulesets       -> 403
    DELETE /repos/rohox/agent-probe              -> 403

    I cannot write to your personal repos, cannot create repos under your account, and cannot create or remove rulesets anywhere. So I also cannot undo protections you add later.

    Two things left:


    Main inside rohox is not protected. I pushed straight to main on agent-probe. If you want it gated there, you add a ruleset, since the token can't.
    Nothing gives me access to your own repos yet. That's a separate credential whenever you want it.


    rohox/agent-probe is still there, private. I can't delete it.
    rohan.adwankar  [9:10 PM]
     Main inside rohox is not protecteddont care
    Nothing gives me access to your own repos yetwhat are you tlaking abotu
    oxroute  [9:11 PM]
    Finished the org half and marked it done.

    What I did:


    Stored the token in ~/.git-credentials with credential.helper store, so pushes work without putting the token in the URL. Verified with a clean clone, commit, and push to rohox/agent-probe — no inline token anywhere.
    Deleted the leftovers from the designs we abandoned: the ssh key and ~/.ssh/config, and the GitHub App credential helper. Kept ~/.local/bin/agent-github-setup, since that is what applies rulesets if you ever grant administration.
    Wrote two memory files so a future session doesn't re-derive all this: the access setup, and the verified GitHub facts (deploy keys can't bypass rulesets, a PAT inherits your admin bypass, apps can't create repos in a personal account, rulesets on public repos are world-readable).

So not only did it take 10 minutes to do this check with an absurd amount of token wastage and was super hard to read.

## What's Going Wrong

1. Univerals are Always Wrong with the exception of the univeral that universals are always wrong

    It incorrectly claimed "that token has no write permissions on anything"

    I think this is a great example of how the aesthetic style with which Claude writes generate logical errors.

    Claude loves to throw in random univerals because humans like to do it to make their writing more emphatic and interesting but they aren't good for speaking clearly. 
    
2. Tangents and Naval Gazing 

    "one thing that nearly fooled me:" and all the ensuing blabbering delivers no value to the user and does not need to stated.

3. Contrastive Parralelism and 

    "admin isn't for my work — it's for installing the guardrail against me."

    This sentence means absolutely nothing.
    For one, the contrastive parralelism is not productive. Instead of saying what thing are it say what it isn't which inherenly doubles the verbosity.

4. Random Sentence structure 

<might be good to try to measure cataphora rates>

    Back to the prior example, what is "the guardrail"?

    When someone explains something well the ordering of the words is informed by the intention of the sentence. 
    However when Claude speaks it outputs the serntences in random orders such that you do not have the reference. 
    Sort of like in programming if an object is referenced before it is defined.
    Ofcourse unliek programming referencing an object before it is defined is actually fine in natural language
        Eg.) Before she entered the room, Alice took a deep breath        
    I like reading books which have fun with sentence structure but authors use these techniques with specific intention, perhaps building intrigue.

So to recap

    Here's an example of how a human speaks:

        "Get out the way! The apple is going to hit you"

        In this case the human prioritize the most important clause due to the time urgency, then follows with the explanation.
        In the explanation the human prioritizes the apple because it is the reason the person should move.

    Here's how Claude speaks

        "The reason for moving isnt just to defy inerta - it's because I can't be complicit with the impact. 
         Your head is currenly undeneath a tree, the same tree which had an apple. 
         That very apple is currently failling - and that is exactly the kind of thing you would want to avoid.
         There has never been a good reason to stay in the same place."
         
        Here everything is completely wrong. 
        The structure is random with no thoght to priority or order of reference
        The contents are not focused on what are relevant to the speaker, and contains random internal reasoning semgents "the idea of being complicit".
        It leads with some strange negation

Now this is interesting because we can actually analyze this effect with linguistics.
If we compose Claude's sentence into Syntax trees you will notice that we see a greater proportion of the DPs arranged leftward 
Human writing by contrast defines the DPs so that the ensuing sentence in interpretable for someone reading left to right.

<This is just a guess from my part will need to verify, perhaps do some LL parsing thing?>

## Solutions

## Evals


