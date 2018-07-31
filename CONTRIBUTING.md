Contributing to CellLocator
===============================

There are many ways to contribute to CellLocator.

  * Submit a feature request or bug, or add to the discussion on the [CellLocator issue tracker][is]
  * Submit a [Pull Request][pr] to improve CellLocator.

The PR Process, and Related Gotchas
-----------------------------------

#### How to submit a PR ?

If you are new to CellLocator development and you don't have push access to the CellLocator
repository, here are the steps:

1. [Fork and clone][fk] the repository.
3. Create a branch.
4. [Push][push] the branch to your GitHub fork.
5. Create a [Pull Request][pr].

This corresponds to the `Fork & Pull Model` mentioned in the [GitHub flow](https://guides.github.com/introduction/flow/index.html)
guides.

If you have push access to this repository, you could simply push your branch
and create a [Pull Request][pr]. This corresponds to the `Shared Repository Model`
and will facilitate other developers to checkout your topic without having to
[configure a remote](https://help.github.com/articles/configuring-a-remote-for-a-fork/).
It will also simplify the workflow when you are _co-developing_ a branch.

When submitting a PR, make sure to add a `Cc: @cell-locator/developers` comment to
notify CellLocator developers of your awesome contributions. Based on the
comments posted by the reviewers, you may have to revisit your patches.

### How to integrate a PR ?

Getting your contributions integrated is relatively straightforward, here
is the checklist:

* All tests pass
* Consensus is reached. This usually means that at least one reviewer added a `LGTM` comment
and a reasonable amount of time passed without anyone objecting. `LGTM` is an
acronym for _Looks Good to Me_.

Next, there are two scenarios:
* You do NOT have push access: A CellLocator core developer will integrate your PR.
* You have push access: Simply click on the "Merge pull request" button.

Then, click on the "Delete branch" button that appears afterward.


[fk]: http://help.github.com/forking/
[push]: https://help.github.com/articles/pushing-to-a-remote/
[pr]: https://github.com/BICCN/cell-locator/merge_requests
[is]: https://github.com/BICCN/cell-locator/issues
