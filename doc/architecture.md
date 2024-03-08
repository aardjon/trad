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

## Financial budget

As we are doing this in our free time and without anyone paying for the app, we do not want to
spent valuable amounts of money for development and/or operation.

## Time budget

Because this is a hobby project, there is no strict time schedule to provide certain features 
and no pressure to maintain a certain release date. On the other hand, we want to keep time
overhead for things like consultations or software maintenance as low as possible to concentrate
on feature development.

## Learning and fun as decision criteria

Some decicions may not be purely based on technical needs or requirements but also on the
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


# 12. Glossary

## 12.1 Important terms

- Grade: Difficulty of a climbing route, measured e.g. with UIAA or Saxon scale.
- Knowledgebase: Encyclopaedia with climbing related information, e.g. regulations or knots.
- Route: The path by which a climber reaches the top of a mountain.

## 12.2 Translations

|  English             |  German             |
|----------------------|---------------------|
| Grade                | Schwierigskeitsgrad |
| Journal              | Logbuch             |
| Climbing regulations | Kletterregeln       |
| (Climbing) Route     | Kletterweg          |
