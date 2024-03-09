Architecture Documentation
==========================

This documents the architectural views and decisions of the trad application. Its structure is based on the [Arc42](https://arc42.org/overview) documentation template, please follow this template if appropriate when modifying.

# 1. Introduction and Goals

## 1.1 Requirements Overview

Mobile (Android) app providing some handy tools for climbers in the Saxon Switzerland area:
 - Personal climbing journal
 - Climbing route database including community ratings and remarks (based on external sites)
 - Knowledgebase providing useful information (e.g. knot database, climbing regulations)

All of these tools can be used without a working internet connection.

Please refer to [Requirements & Goals](requirements.md) for further information about functional
requirements.

## 1.2 Quality goals

To be defined!

## 1.3 Stakeholders

| Stakeholder       | Contact    | Expectations
|-------------------|------------|-------------
| Developer         | Headbucket |
| Developer         | Aardjon    | Create a full software architecture (+documentation) "the right way" to get some experience.
| External Operator | ???        |


# 2. Architecture Constraints

## Financial and time budget

As we are doing this in our free time and without anyone paying for the app, we do not want to
spent valuable amounts of money for development and/or operation. On the other hand, there is
no strict time schedule to provide certain features and no pressure to maintain a certain
release date.

## Learning and fun as decision criteria

Some decisions may not be purely based on technical needs or requirements but also on the
opportunity to learn something new or to have fun using a certain software. So these are valid
decision criteria for this project.

## Limited network access

In the mountains there often is no or very low internet access. That's why the mobile app must
not depend on a working internet connection for regular operation.

## Privacy protection

When handling personal data (if any) we have to conform to the german/EU privacy laws. Journal
data must be kept locally.

## Copyright concerns

Mirroring data from external sites may touch copyright regulations that need to be respected.

## Licenses

To keep the door open for publishing on F-Droid later on, trad and all its dependencies must be
licensed as FLOSS (free, libre and open source software).


# 3. Context and scope

## 3.1 Business context

![Business context diagram, showing external data flows](contextview_business.png)

## 3.2 Technical context

![Technical context diagram, showing external dependencies](contextview_technical.png)


# 9. Architecture Decisions


# 10. Quality Requirements

These are the quality requirements we explicitly want to fulfil as good as possible, ordered by
priority ("1" being "most important"):


 ID | Prio | Quality Properties | Requirement
----|------|--------------------|-------------------------
QREQ-1  | 1 | Flexibility, Maintainability | It shall be easy to implement new/changed use cases/features without interfering with exiting code more than necessary.
QREQ-2  | 1 | Maintainability, Testability | The necessity for manual testing (e.g. regressions tests) must be kept as low as possible.
QREQ-3  | 1 | Reliability, Usability | All "in the mountains" use cases must be fully functional without any network connection.
QREQ-4  | 1 | Reliability, Durability | (Exported) journal data shall be importable by any future application version.
QREQ-5  | 1 | Compliance | It must comply with all (german) laws (esp. copyright and privacy).
QREQ-6  | 2 | Maintainability | It shall be possible to upgrade external dependencies with as less effort as possible.
QREQ-7  | 2 | Adaptability | It shall be possible to adopt to changes of external interfaces with as less effort as possible.
QREQ-8  | 2 | Compliance, Performance | Data from external interfaces must only be requested if really necessary (to keep their traffic as low as possible).
QREQ-9  | 2 | Compliance, Performance | The traffic on external interfaces shall not increase with the number of app users.
QREQ-10 | 2 | Compliance, Security | Personal data must always be saved locally and only exported/uploaded with explicit agreement.
QREQ-11 | 2 | Security | Journal data must be handled very sensitively and it must be prevented at all costs that it is accidentally deleted.
QREQ-12 | 3 | Security | The app shall only request the permissions that are really needed by the use cases.
QREQ-13 | 3 | Usability | Device permissions shall only be requested when they are needed (first time).
QREQ-14 | 4 | Security, Usability | A denied permission must not prevent use cases that do not depend on it.
QREQ-15 | 4 | Transferability | It shall be easily possible to add a new destination platform.


# 12. Glossary

## 12.1 Important terms

- Grade: Difficulty of a climbing route, measured e.g. with UIAA or Saxon scale.
- Knowledgebase: Encyclopaedia with climbing related information, e.g. regulations or knots.
- Route: The path by which a climber reaches the top of a mountain.
- Summit: The destination of a climbing route, usually the highest point of a single rock or mountain.

## 12.2 Translations

|  English             |  German             |
|----------------------|---------------------|
| Grade                | Schwierigskeitsgrad |
| Journal              | Logbuch             |
| Climbing regulations | Kletterregeln       |
| (Climbing) Route     | Kletterweg          |
| Summit               | Gipfel              |
