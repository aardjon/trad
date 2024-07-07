# Flutter UI Documentation

The Flutter based UI is implemented within the `infrastructure.flutter.ui` component. It is
recommended to read the chapter [UI state propagation/management](https://docs.flutter.dev/data-and-backend/state-mgmt)
in the official Flutter documentation to better understand this component.

## Implementation rules and guidelines

 - Be as dumb as possible
 - Don't do any data interpretation, conversion or reformatting
 - The `adapters.boundaries.ui` interface provides basic Dart types like `String` and `bool` only (`enum`s or `int` are possible for special cases)
 - All widgets (and also the UI as a whole) should preferably be stateless whenever possible
 - The `StatefulWidget` class is probably the wrong tool in most situations
 - We are using the [provider](https://pub.dev/packages/provider) package for state propagation, as recommended by the Flutter documentation

## State handling

The UI does not have any externally visible state. But it may have some internal, UI only state if
necessary, which is limited to the `infrastructure.flutter` ring. This internal state would be what
the official Flutter documentation refers to as "app state". The also mentioned "ephemeral state"
is limited to a single widget (i.e. a `StatefulWidget`) and is only relevant for special cases.

## When to use `StatefulWidget`s?

`StatefulWidget`s are widgets containing some logic and state data of their own, it is very
difficult to separate UI and external business logic when using them. This is because they are
meant to be used for handling "ephemeral states" only. So in the vast majority of `trad`s UI use
cases this is not necessary, but a `StatefulWidget` may be considered if all of the following
conditions are met:
 - The widget is self-contained, i.e. must contain all necessary logic and data (e.g. in a widget library)
 - The widget needs to "change" (=rebuild) due to widget data/state change triggered by a user action
 - The data change/redraw is *no* application business logic but only relevant within this single widget

Possible examples for such widgets:
 - Date picker: The application wants the user to enter a date. Whether this is a plain text field or some more advanced calender tool is an implementation detail.
 - Number picker: The application wants the user to enter a number within a certain range. The UI may use a text field which only allows integer numbers as input, and provides increase/decrease buttons.
