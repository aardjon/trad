# Knowledge Base Documentation

## Refined Requirements

 1. There shall be a wiki-like collection of text documents that can be displayed.
 2. When accessed, an index listing available documents shall be shown. 
 3. When the user clicks a link to another document, it shall be displayed instead of the current one.
 4. When displaying a document, formatted text and referenced images shall be rendered correctly. 

## Document File Format Specification

All document files as well as additional resources (such as image files) have to be stored within the [assets/knowledgebase](https://github.com/Headbucket/trad/tree/knowledgebase-documentation/mobileapp/infrastructure_flutter/assets/knowledgebase) directory of the *infrastructure_flutter*  package. The index document is named `index.md`. Furthermore, all files must be listed in the `flutter/assets` section of this packages [pubspec.yaml](https://github.com/Headbucket/trad/blob/knowledgebase-documentation/mobileapp/infrastructure_flutter/pubspec.yaml) file. 

A document file is a text file using [Github Flavoured Markdown](https://github.github.com/gfm/) for text formatting. Before the actual document content, **the very first line** contains the document's title which is rendered separately and is not a part of the section hierarchy. Therefore, this header line can be of any hierarchy level (or none at all). The actual (rendered) content starts with the second line. Example:

```Markdown
# Page title that is not rendered as part of the content but displayed separately.
# Page content starts here with a main header. This is the first rendered line. 
## Section 1
## Section 2
```

When linking to other documents, the destination path must be prefixed with `packages/infrastructure_flutter/assets/knowledgebase`. When embedding images, the destination path must be prefixed with `resource:packages/infrastructure_flutter/assets/knowledgebase`:

```Markdown
[Link to example document](packages/infrastructure_flutter/assets/knowledgebase/example.md)

![Some example image](resource:packages/infrastructure_flutter/assets/knowledgebase/example.jpg)
```

Referencing external sources or absolute paths is not allowed.
