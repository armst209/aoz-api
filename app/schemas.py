
from enum import Enum
from typing import Optional, Union
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


# Some spec values are plain numbers, others are annotated strings
# like "3040 (+410 kW)" or "94.2 (MS mode), 94.7 (MA mode)".
NumberOrText = Union[float, str]


class CamelModel(BaseModel):
    """Base model that reads/writes camelCase JSON keys while using snake_case in Python."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class UnitType(str, Enum):
    """Broad classification of a mobile weapon: mobile suit, mobile armor, or other weapon."""

    MOBILE_SUIT = "Mobile Suit"
    MOBILE_ARMOR = "Mobile Armor"
    WEAPON = "Weapon"


class Production(str, Enum):
    """Production status of a unit, from one-off prototype to mass production."""

    PROTOTYPE = "Prototype"
    LIMITED_PRODUCTION = "Limited Production"
    MASS_PRODUCTION = "Mass Production"


class Specs(CamelModel):
    """Technical specifications of a mobile weapon (dimensions, power, armor, thrusters, etc.)."""

    height_m: Optional[NumberOrText] = None
    head_height_m: Optional[float] = None
    weight_t: Optional[NumberOrText] = None
    empty_weight_t: Optional[float] = None
    power_output_kw: Optional[NumberOrText] = None
    powerplant: Optional[str] = None
    armor: list[str] = Field(default_factory=list)
    sensor_range_m: Optional[int] = None
    max_acceleration_g: Optional[NumberOrText] = None
    mass_ratio: Optional[NumberOrText] = None
    turn_time_sec: Optional[float] = None
    rocket_thrusters_kg: list[str] = Field(default_factory=list)
    vernier_thrusters: Optional[int] = None
    thruster_layout: list[str] = Field(default_factory=list)


class Equipment(CamelModel):
    """Standard and optional equipment carried by a unit."""

    standard: list[str] = Field(default_factory=list)
    optional: list[str] = Field(default_factory=list)


class Armaments(CamelModel):
    """Fixed and handheld weapons, including optional loadouts."""

    fixed: list[str] = Field(default_factory=list)
    handheld: list[str] = Field(default_factory=list)
    optional_fixed: list[str] = Field(default_factory=list)
    optional_handheld: list[str] = Field(default_factory=list)


class Image(CamelModel):
    """An image file with an optional caption."""

    file: str
    caption: Optional[str] = None


class MobileWeapon(CamelModel):
    """A mobile suit, mobile armor, or other mobile weapon and its full profile."""

    id: str
    name: str
    model_number: str
    codename: Optional[str] = None
    faction: str
    other_names: list[str] = Field(default_factory=list)
    japanese_name: Optional[str] = None
    summary: Optional[str] = None
    unit_type: UnitType
    production: Production
    usage: Optional[str] = None
    specialization: Optional[str] = None
    environment: Optional[str] = None
    transformable: Optional[bool] = None
    first_deployed: Optional[str] = None
    last_deployed: Optional[str] = None
    era: str
    designers: list[str] = Field(default_factory=list)
    developed_from: list[str] = Field(default_factory=list)
    manufacturers: list[str] = Field(default_factory=list)
    operators: list[str] = Field(default_factory=list)
    pilots: list[str] = Field(default_factory=list)
    cockpit: Optional[str] = None
    specs: Specs = Field(default_factory=Specs)
    equipment: Equipment = Field(default_factory=Equipment)
    armaments: Armaments = Field(default_factory=Armaments)
    appearances: list[str] = Field(default_factory=list)
    image: Optional[str] = None
    image_url: Optional[str] = None
    images: list[Image] = Field(default_factory=list)
    wiki_url: Optional[str] = None
    source_page: Optional[str] = None
    source_section: Optional[str] = None
    is_variant_of: Optional[str] = None
    extra: dict[str, str] = Field(default_factory=dict)


class SupportWeaponCategory(str, Enum):
    """Kind of support weapon: ship, vehicle, or pod."""

    SHIP = "Ship"
    VEHICLE = "Vehicle"
    POD = "Pod"


class SupportWeaponSpecs(CamelModel):
    """Technical specifications of a support weapon (dimensions, power, propulsion, armor)."""

    height_m: Optional[NumberOrText] = None
    length_m: Optional[NumberOrText] = None
    width_m: Optional[NumberOrText] = None
    weight_t: Optional[NumberOrText] = None
    power_output_kw: Optional[NumberOrText] = None
    powerplant: Optional[str] = None
    propulsion: list[str] = Field(default_factory=list)
    armor: list[str] = Field(default_factory=list)


class ComplementGroup(CamelModel):
    """A named group of mobile suits carried as part of a ship's complement."""

    group: str
    units: list[str] = Field(default_factory=list)


class MobileSuitOperations(CamelModel):
    """Mobile suit carrying capability of a support weapon: hangars, catapults, capacity, and complement."""

    hangars: Optional[int] = None
    catapults: Optional[int] = None
    # Either a count or a range such as "8-12".
    capacity: Optional[Union[int, str]] = None
    complement: list[ComplementGroup] = Field(default_factory=list)


class SupportWeapon(CamelModel):
    """A ship, vehicle, or pod that supports mobile suit operations, and its full profile."""

    id: str
    name: str
    model_number: Optional[str] = None
    codename: Optional[str] = None
    faction: str
    other_names: list[str] = Field(default_factory=list)
    japanese_name: Optional[str] = None
    summary: Optional[str] = None
    category: SupportWeaponCategory
    classification: Optional[str] = None
    production: Optional[Production] = None
    usage: Optional[str] = None
    specialization: Optional[str] = None
    environment: Optional[str] = None
    transformable: Optional[bool] = None
    first_deployed: Optional[str] = None
    last_deployed: Optional[str] = None
    debut: Optional[str] = None
    era: str
    designers: list[str] = Field(default_factory=list)
    developed_from: list[str] = Field(default_factory=list)
    manufacturers: list[str] = Field(default_factory=list)
    operators: list[str] = Field(default_factory=list)
    pilots: list[str] = Field(default_factory=list)
    captains: list[str] = Field(default_factory=list)
    crew: list[str] = Field(default_factory=list)
    ships_of_the_line: list[str] = Field(default_factory=list)
    specs: SupportWeaponSpecs = Field(default_factory=SupportWeaponSpecs)
    mobile_suit_operations: MobileSuitOperations = Field(
        default_factory=MobileSuitOperations)
    equipment: Equipment = Field(default_factory=Equipment)
    armaments: Armaments = Field(default_factory=Armaments)
    appearances: list[str] = Field(default_factory=list)
    image: Optional[str] = None
    image_url: Optional[str] = None
    images: list[Image] = Field(default_factory=list)
    wiki_url: Optional[str] = None
    source_page: Optional[str] = None
    extra: dict[str, str] = Field(default_factory=dict)


class KitType(str, Enum):
    """What a model kit contains: a full unit, add-on parts, a conversion kit, or a bundle."""

    FULL_KIT = "Full Kit"
    EXPANSION_SET = "Expansion Set"
    CONVERSION_KIT = "Conversion Kit"
    MULTI_KIT_SET = "Multi-Kit Set"


class Distribution(str, Enum):
    """How a model kit was sold."""

    GENERAL_RETAIL = "General Retail"
    PREMIUM_BANDAI = "Premium Bandai"
    THE_GUNDAM_BASE = "The Gundam Base"
    GUNDAM_SIDE_F = "Gundam Side-F"
    MAGAZINE_GIVEAWAY = "Magazine Giveaway"
    MAIL_ORDER = "Mail Order"


class Price(CamelModel):
    """Original retail price of a model kit."""

    amount: int
    currency: str = "JPY"
    tax_included: bool = False


class KitUnit(CamelModel):
    """A unit depicted by a model kit, linked to its Mobile/Support Weapon entry if one exists."""

    name: str
    form: Optional[str] = None
    mobile_weapon_id: Optional[str] = None
    support_weapon_id: Optional[str] = None


class Reissue(CamelModel):
    """A later re-release of a model kit."""

    date: str
    note: Optional[str] = None


class ModelKit(CamelModel):
    """A Gunpla or garage kit release for Advance of Zeta / A.O.Z Re-Boot."""

    id: str
    name: str
    japanese_name: Optional[str] = None
    series: str
    other_series: list[str] = Field(default_factory=list)
    line: str
    grade: Optional[str] = None
    # Usually a single scale such as "1/144"; "Mixed" for multi-scale sets.
    scale: str
    product_number: Optional[str] = None
    kit_type: KitType
    material: str = "Plastic"
    manufacturer: str
    distribution: Distribution
    exclusive: bool
    # "YYYY-MM" (or "YYYY" when only the year is known).
    release_date: str
    price: Optional[Price] = None
    transformable: bool = False
    units: list[KitUnit] = Field(default_factory=list)
    # Ids of the kits this one is a parts/color variant of.
    based_on: list[str] = Field(default_factory=list)
    # Ids of the kits needed to build this one (for expansion sets).
    requires: list[str] = Field(default_factory=list)
    reissues: list[Reissue] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    image: Optional[str] = None
    image_url: Optional[str] = None
    wiki_url: Optional[str] = None
    source_page: Optional[str] = None
    extra: dict[str, str] = Field(default_factory=dict)


class CharacterGroup(str, Enum):
    """The group a character is listed under on the series page."""

    TITANS_TEST_TEAM = "Titans Test Team (T3)"
    EARTH_FEDERATION = "Earth Federation"
    AEUG = "AEUG"
    ZEON_REMNANTS = "Zeon Remnants"
    OTHER = "Other"


class UnitRole(str, Enum):
    """How a character is associated with a unit."""

    PILOT = "pilot"
    CREW = "crew"
    CAPTAIN = "captain"


class AssociatedUnit(CamelModel):
    """A unit a character pilots, crews, or captains, linked to its Mobile/Support Weapon entry."""

    name: str
    role: UnitRole
    note: Optional[str] = None
    mobile_weapon_id: Optional[str] = None
    support_weapon_id: Optional[str] = None


class Character(CamelModel):
    """A character from Advance of Zeta and their profile."""

    id: str
    slug: str
    name: str
    japanese_name: Optional[str] = None
    romanized_name: Optional[str] = None
    group: CharacterGroup
    # Description of the character from the series page.
    role: Optional[str] = None
    summary: Optional[str] = None
    species: Optional[str] = None
    gender: Optional[str] = None
    # A plain number or annotated text such as "23 (U.C. 0084)".
    age: Optional[Union[int, str]] = None
    birthdate: Optional[str] = None
    deathdate: Optional[str] = None
    # e.g. "Alive" or "Killed In Action (February U.C.0088)".
    status: Optional[str] = None
    nationality: Optional[str] = None
    affiliations: list[str] = Field(default_factory=list)
    occupations: list[str] = Field(default_factory=list)
    rank: Optional[str] = None
    era: Optional[str] = None
    appearances: list[str] = Field(default_factory=list)
    associated_units: list[AssociatedUnit] = Field(default_factory=list)
    image: Optional[str] = None
    image_url: Optional[str] = None
    images: list[Image] = Field(default_factory=list)
    has_wiki_page: bool = False
    wiki_url: Optional[str] = None
