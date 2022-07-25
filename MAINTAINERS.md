# Maintainers

## Making a release

A core developer should use the following steps to create a release of **Cell Locator**

1. Update [CHANGES.md][changes] adding missing entries in `Next Release` section

2. Remote connect to `overload` windows build machine (internally hosted at Kitware)

3. Open `Git Bash` and update source checkout

    ```
    cd /d/D/P/CL-0
    git pull origin master
    ```

4. Run `D:\D\DashboardScripts\overload-vs2019-cell-locator_preview_experimental.bat` script

    _Scripts are available at https://github.com/Slicer/DashboardScripts__

5. From the developer workstation, tag the release:

    ```
    release=X.Y.Z-YYYY-MM-DD
    git tag --sign -m "${release}" ${release} master
    git push origin ${release}
    ```

    where:

    * `X.Y.Z` corresponds to the version in [Applications/CellLocatorApp/slicer-application-properties.cmake](https://github.com/BICCN/cell-locator/blob/master/Applications/CellLocatorApp/slicer-application-properties.cmake)
    * `YYYY-MM-DD` corresponds to the date of commit from which the application is built

    _We recommend using a [GPG signing key](https://help.github.com/articles/generating-a-new-gpg-key/) to sign the tag._

6. From the developer workstation:

  * update [CHANGES.md][changes] replacing `Next Release` with `Cell Locator X.Y.Z-YYYY-MM-DD` and push.
  * update `AnnotationFileFormat.md` based on the [Annotation File Format Versioning Guidelines]][annotation-file-format-versioning-guidelines] and push.

7. Go to [https://github.com/BICCN/cell-locator/tags](https://github.com/BICCN/cell-locator/tags), then create a _release_ or _pre-release_ from the tag.

   Update release description to include text like the following:

   ```
   See [release notes](https://github.com/BICCN/cell-locator/blob/master/CHANGES.md#cell-locator-XYZ-YYYY-MM-DD)
   ```

   where `XYZ-YYYY-MM-DD` should corresponds to the `release` set in previous steps.

8. From the build machine, login to GitHub and upload the package as a release asset.

[changes]: https://github.com/BICCN/cell-locator/blob/master/CHANGES.md
[annotation-file-format-versioning-guidelines]: https://github.com/BICCN/cell-locator/blob/master/Documentation/developer_guide/AnnotationFileFormat.md#versioning-guidelines
