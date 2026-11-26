"""Professional Editor: installation profile (prototype Tela 2)."""

from __future__ import annotations

import html
import logging
import uuid
from pathlib import Path
from typing import cast

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from cranioz.application.professional import (
    ProfessionalQueries,
    UpdateProfessionalProfileCommand,
)
from cranioz.domain.professional import (
    Address,
    ProfessionalProfile,
    ProfessionalRegistration,
)
from cranioz.editors.builtin.professional.settings import ProfessionalEditorSettings
from cranioz.editors.core.editor.base_editor import Editor
from cranioz.editors.core.editor.editor_context import EditorContext
from cranioz.infrastructure.settings.protocol import SettingsService
from cranioz.ui.widgets.forms import (
    FilePicker,
    FilePickerMode,
    FormCombo,
    FormField,
    FormRow,
    SignaturePreview,
)
from cranioz.ui.widgets.sections import CollapsibleSection, DragList

_logger = logging.getLogger(__name__)

PROFESSIONAL_EDITOR_ID = "editor.professional"
PROFESSIONAL_QUERIES_EXTRA = "professional_queries"
PROFESSIONAL_SETTINGS_EXTRA = "professional_settings"
_TOP_BAR_CLEARANCE_PX = 56


class _ProfessionalEditorSignals(QObject):
    profile_saved = Signal(object)
    save_failed = Signal(str)


class ProfessionalEditor(Editor):
    """Edit and preview the installation Professional profile."""

    def __init__(
        self,
        editor_id: str = PROFESSIONAL_EDITOR_ID,
        title: str = "Professional",
    ) -> None:
        super().__init__(editor_id=editor_id, title=title)
        self._professional_signals = _ProfessionalEditorSignals()
        self.profile_saved = self._professional_signals.profile_saved
        self.save_failed = self._professional_signals.save_failed

        self._context: EditorContext | None = None
        self._queries: ProfessionalQueries | None = None
        self._settings: ProfessionalEditorSettings | None = None
        self._loaded_profile: ProfessionalProfile | None = None
        self._content: QWidget | None = None
        self._status_label: QLabel | None = None
        self._preview: QLabel | None = None
        self._save_button: QPushButton | None = None
        self._cancel_button: QPushButton | None = None

        self._salutation: FormField | None = None
        self._full_name: FormField | None = None
        self._preferred_name: FormField | None = None
        self._email: FormField | None = None
        self._phone: FormField | None = None
        self._practice_name: FormField | None = None
        self._authority: FormField | None = None
        self._registration_number: FormField | None = None
        self._region_code: FormField | None = None
        self._regional_profile: FormCombo | None = None
        self._document_language: FormCombo | None = None
        self._postal_code: FormField | None = None
        self._street: FormField | None = None
        self._number: FormField | None = None
        self._complement: FormField | None = None
        self._district: FormField | None = None
        self._city: FormField | None = None
        self._state: FormField | None = None
        self._country: FormField | None = None
        self._logo: FilePicker | None = None
        self._signature: FilePicker | None = None
        self._signature_preview: SignaturePreview | None = None
        self._sections: dict[str, CollapsibleSection] = {}
        self._section_list: DragList | None = None

    # ----- Lifecycle -------------------------------------------------

    def initialize(self, context: EditorContext) -> None:
        self._context = context
        queries = context.extras.get(PROFESSIONAL_QUERIES_EXTRA)
        if isinstance(queries, ProfessionalQueries):
            self._queries = queries
        elif queries is not None:
            _logger.warning(
                "ProfessionalEditor ignored invalid professional_queries extra: %s",
                type(queries).__name__,
            )

        settings = context.extras.get(PROFESSIONAL_SETTINGS_EXTRA)
        if settings is not None:
            self._settings = ProfessionalEditorSettings(cast(SettingsService, settings))

    def activate(self) -> None:
        if self._settings is not None:
            self._settings.set_last_section("professional")

    def dispose(self) -> None:
        super().dispose()
        if self._content is not None:
            self._content.setParent(None)
            self._content.deleteLater()
        self._content = None
        self._context = None
        self._queries = None
        self._settings = None
        self._loaded_profile = None
        self._sections.clear()
        self._section_list = None

    # ----- Content ---------------------------------------------------

    def content_widget(self) -> QWidget:
        if self._content is None:
            self._content = self._build_content()
            self._reload_profile()
        return self._content

    @property
    def loaded_profile(self) -> ProfessionalProfile | None:
        return self._loaded_profile

    @property
    def preview_text(self) -> str:
        return "" if self._preview is None else self._preview.text()

    def save_profile(self) -> ProfessionalProfile | None:
        """Validate, dispatch, and return the saved profile."""
        if self._save_button is None:
            raise RuntimeError("content_widget() must be called before save_profile()")
        dispatcher = self._context.command_dispatcher if self._context is not None else None
        if dispatcher is None:
            message = self._tr(
                "professional.profile.save_unavailable",
                "Profile saving is unavailable because the command dispatcher is missing.",
            )
            self._set_status(message, error=True)
            self.save_failed.emit(message)
            return None

        try:
            profile = self._profile_from_fields()
        except (TypeError, ValueError) as exc:
            self._set_status(str(exc), error=True)
            self.save_failed.emit(str(exc))
            return None

        self._save_button.setEnabled(False)
        try:
            result = dispatcher.dispatch(UpdateProfessionalProfileCommand(profile=profile))
        except Exception as exc:
            _logger.exception("cannot save Professional profile")
            message = self._tr(
                "professional.profile.save_failed",
                "The profile could not be saved: {detail}",
                detail=str(exc),
            )
            self._set_status(message, error=True)
            self.save_failed.emit(message)
            return None
        finally:
            if self._save_button is not None:
                self._save_button.setEnabled(True)

        saved = result if isinstance(result, ProfessionalProfile) else profile
        self._loaded_profile = saved
        self._set_status(
            self._tr("professional.profile.saved", "Profile saved."),
            error=False,
        )
        self._update_preview()
        self.profile_saved.emit(saved)
        return saved

    def cancel_changes(self) -> None:
        self._reload_profile()

    # ----- Layout ----------------------------------------------------

    def _build_content(self) -> QWidget:
        root = QWidget()
        root.setObjectName("professional_editor.content")
        layout = QVBoxLayout(root)
        # The Workspace Top Bar overlays the top of the Central Area.
        layout.setContentsMargins(16, _TOP_BAR_CLEARANCE_PX, 16, 12)
        layout.setSpacing(12)

        title = QLabel(self._tr("professional.profile.title", "Professional profile"))
        title.setProperty("role", "title")
        subtitle = QLabel(
            self._tr(
                "professional.profile.subtitle",
                "Information used in documents generated by CranioZ.",
            )
        )
        subtitle.setProperty("role", "subtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(subtitle)

        columns = QHBoxLayout()
        columns.setSpacing(12)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(self._build_form())
        columns.addWidget(scroll, 3)
        columns.addWidget(self._build_preview_panel(), 2)
        layout.addLayout(columns, 1)
        layout.addLayout(self._build_footer())

        self._connect_form_signals()
        return root

    def _build_form(self) -> QWidget:
        self._salutation = self._field("profile.salutation", "Salutation")
        self._full_name = self._field("profile.full_name", "Surgeon's name")
        self._preferred_name = self._field("profile.preferred_name", "Preferred name")
        self._email = self._field("profile.email", "Email")
        self._phone = self._field("profile.phone", "Telephone")
        self._practice_name = self._field("profile.practice_name", "Practice name")

        self._authority = self._field("profile.authority", "Registration authority")
        self._registration_number = self._field(
            "profile.registration_number",
            "Registration number",
        )
        self._region_code = self._field("profile.region_code", "Registration region")
        self._regional_profile = FormCombo(
            self._tr("professional.profile.regional_profile", "Regional profile")
        )
        self._regional_profile.setObjectName("professional.profile.regional_profile")
        self._regional_profile.add_items((("Brasil (BR)", "BR"), ("Generic", "GENERIC")))
        self._document_language = FormCombo(
            self._tr("professional.profile.document_language", "Document language")
        )
        self._document_language.setObjectName("professional.profile.document_language")
        self._document_language.add_items((("Português (Brasil)", "pt-BR"), ("English", "en")))

        self._postal_code = self._field("profile.postal_code", "Postal code")
        self._street = self._field("profile.street", "Street")
        self._number = self._field("profile.address_number", "Number")
        self._complement = self._field("profile.complement", "Complement")
        self._district = self._field("profile.district", "District")
        self._city = self._field("profile.city", "City")
        self._state = self._field("profile.state", "State")
        self._country = self._field("profile.country", "Country")

        self._logo = FilePicker(
            self._tr("professional.profile.clinic_logo", "Clinic logo"),
            mode=FilePickerMode.OPEN_FILE,
        )
        self._logo.setObjectName("professional.profile.clinic_logo")
        self._signature = FilePicker(
            self._tr("professional.profile.digital_signature", "Surgeon's digital signature"),
            mode=FilePickerMode.OPEN_FILE,
        )
        self._signature.setObjectName("professional.profile.digital_signature")
        self._signature_preview = SignaturePreview()
        self._signature_preview.setObjectName("professional.profile.signature_preview")

        page = QWidget()
        page.setObjectName("professional_editor.form")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        section_list = DragList()
        section_list.setObjectName("professional.profile.sections")
        section_list.add_section(
            "identification",
            self._section(
                "identification",
                self._tr("professional.profile.identification", "Professional identification"),
                (
                    self._row(self._salutation, self._full_name, stretches=(1, 3)),
                    self._row(self._preferred_name, self._email),
                    self._row(self._phone, self._practice_name),
                ),
            ),
        )
        section_list.add_section(
            "registration",
            self._section(
                "registration",
                self._tr("professional.profile.registration_section", "Professional registration"),
                (
                    self._row(self._authority, self._registration_number),
                    self._row(self._region_code, self._regional_profile),
                    self._row(self._document_language),
                ),
            ),
        )
        section_list.add_section(
            "address",
            self._section(
                "address",
                self._tr("professional.profile.address_section", "Address"),
                (
                    self._row(self._postal_code, self._street),
                    self._row(self._number, self._complement),
                    self._row(self._district, self._city, self._state),
                    self._row(self._country),
                ),
            ),
        )
        section_list.add_section(
            "documents",
            self._section(
                "documents",
                self._tr("professional.profile.documents_section", "Documents"),
                (
                    self._logo,
                    self._signature,
                    QLabel(
                        self._tr(
                            "professional.profile.signature_preview",
                            "Surgeon's signature preview",
                        )
                    ),
                    self._signature_preview,
                ),
            ),
        )
        self._section_list = section_list
        self._restore_section_order()
        section_list.order_changed.connect(self._persist_section_order)
        layout.addWidget(section_list)
        layout.addStretch(1)
        return page

    def _build_preview_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("professional_editor.preview")
        panel.setProperty("class", "card")
        panel.setMinimumWidth(280)
        panel.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        heading = QLabel(self._tr("professional.profile.preview_title", "Document preview"))
        heading.setProperty("role", "title")
        layout.addWidget(heading)

        self._preview = QLabel()
        self._preview.setObjectName("professional.profile.preview_content")
        self._preview.setWordWrap(True)
        self._preview.setTextFormat(Qt.TextFormat.RichText)
        self._preview.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self._preview, 1)
        return panel

    def _build_footer(self) -> QHBoxLayout:
        footer = QHBoxLayout()
        self._status_label = QLabel()
        self._status_label.setObjectName("professional.profile.status")
        self._status_label.setWordWrap(True)
        footer.addWidget(self._status_label, 1)

        self._cancel_button = QPushButton(self._tr("professional.profile.cancel", "Cancel"))
        self._cancel_button.setObjectName("professional.profile.cancel")
        self._cancel_button.setProperty("class", "secondary")
        self._cancel_button.clicked.connect(self.cancel_changes)
        footer.addWidget(self._cancel_button)

        self._save_button = QPushButton(self._tr("professional.profile.save", "Save"))
        self._save_button.setObjectName("professional.profile.save")
        self._save_button.clicked.connect(self.save_profile)
        footer.addWidget(self._save_button)

        available = (
            self._context is not None
            and self._context.command_dispatcher is not None
            and self._queries is not None
        )
        self._save_button.setEnabled(available)
        self._cancel_button.setEnabled(self._queries is not None)
        return footer

    def _section(
        self,
        section_id: str,
        title: str,
        children: tuple[QWidget, ...],
    ) -> CollapsibleSection:
        section = CollapsibleSection(title)
        section.setObjectName(f"professional.profile.section.{section_id}")

        body = QWidget()
        body.setObjectName(f"professional.profile.section.{section_id}.body")
        layout = QVBoxLayout(body)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        for child in children:
            layout.addWidget(child)
        section.set_body_widget(body)
        self._sections[section_id] = section
        return section

    def _restore_section_order(self) -> None:
        section_list = self._section_list
        settings = self._settings
        if section_list is None or settings is None:
            return

        current = section_list.keys()
        ordered: list[str] = []
        seen: set[str] = set()
        for key in settings.navigation_order():
            if key in current and key not in seen:
                ordered.append(key)
                seen.add(key)
        ordered.extend(key for key in current if key not in seen)
        if ordered != current:
            section_list.set_order(ordered)

    def _persist_section_order(self, sections: list[str]) -> None:
        if self._settings is None:
            return
        self._settings.set_navigation_order(tuple(sections))

    @staticmethod
    def _row(*widgets: QWidget, stretches: int | tuple[int, ...] = 1) -> FormRow:
        row = FormRow()
        if isinstance(stretches, int):
            stretch_values = (stretches,) * len(widgets)
        else:
            if len(stretches) != len(widgets):
                raise ValueError("one stretch value is required per widget")
            stretch_values = stretches
        for widget, stretch in zip(widgets, stretch_values, strict=True):
            row.add_field(widget, stretch)
        return row

    def _field(self, object_suffix: str, label: str) -> FormField:
        widget = FormField(self._tr(f"professional.{object_suffix}", label))
        widget.setObjectName(f"professional.{object_suffix}")
        return widget

    # ----- Data binding ----------------------------------------------

    def _connect_form_signals(self) -> None:
        for field in (
            self._salutation,
            self._full_name,
            self._preferred_name,
            self._email,
            self._phone,
            self._practice_name,
            self._authority,
            self._registration_number,
            self._region_code,
            self._postal_code,
            self._street,
            self._number,
            self._complement,
            self._district,
            self._city,
            self._state,
            self._country,
        ):
            if field is not None:
                field.text_changed.connect(self._update_preview)
        for combo in (self._regional_profile, self._document_language):
            if combo is not None:
                combo.current_changed.connect(self._update_preview)
        if self._logo is not None:
            self._logo.path_changed.connect(self._update_preview)
        if self._signature is not None:
            self._signature.path_changed.connect(self._on_signature_path_changed)

    def _reload_profile(self) -> None:
        if self._queries is None:
            self._populate_profile(None)
            self._set_status(
                self._tr(
                    "professional.profile.storage_unavailable",
                    "Professional profile storage is unavailable.",
                ),
                error=True,
            )
            return
        try:
            profile = self._queries.get_profile()
        except Exception as exc:
            _logger.exception("cannot load Professional profile")
            self._populate_profile(None)
            self._set_status(
                self._tr(
                    "professional.profile.load_failed",
                    "The profile could not be loaded: {detail}",
                    detail=str(exc),
                ),
                error=True,
            )
            return
        self._populate_profile(profile)
        self._set_status("", error=False)

    def _populate_profile(self, profile: ProfessionalProfile | None) -> None:
        self._loaded_profile = profile
        address = profile.address if profile is not None else Address()
        primary = self._primary_registration(profile)

        self._set_field(self._salutation, profile.salutation if profile else None)
        self._set_field(self._full_name, profile.full_name if profile else None)
        self._set_field(self._preferred_name, profile.preferred_name if profile else None)
        self._set_field(self._email, profile.email if profile else None)
        self._set_field(self._phone, profile.phone if profile else None)
        self._set_field(self._practice_name, profile.practice_name if profile else None)
        self._set_field(self._authority, primary.authority if primary else None)
        self._set_field(
            self._registration_number,
            primary.registration_number if primary else None,
        )
        self._set_field(
            self._region_code,
            primary.region_code if primary else None,
        )
        self._set_combo(
            self._regional_profile,
            profile.regional_profile if profile is not None else "BR",
        )
        self._set_combo(
            self._document_language,
            profile.document_language if profile and profile.document_language else "pt-BR",
        )

        self._set_field(self._postal_code, address.postal_code)
        self._set_field(self._street, address.street)
        self._set_field(self._number, address.number)
        self._set_field(self._complement, address.complement)
        self._set_field(self._district, address.district)
        self._set_field(self._city, address.city)
        self._set_field(self._state, address.state)
        self._set_field(self._country, address.country or "BR")

        self._set_picker(self._logo, profile.logo_reference if profile else None)
        self._set_picker(
            self._signature,
            profile.signature_reference if profile else None,
        )
        self._on_signature_path_changed(self._signature.path if self._signature else "")
        self._update_preview()

    def _profile_from_fields(self) -> ProfessionalProfile:
        full_name = self._required_text(self._full_name, "full_name", "Surgeon's name")
        address = Address(
            postal_code=self._optional_text(self._postal_code),
            street=self._optional_text(self._street),
            number=self._optional_text(self._number),
            complement=self._optional_text(self._complement),
            district=self._optional_text(self._district),
            city=self._optional_text(self._city),
            state=self._optional_text(self._state),
            country=self._optional_text(self._country),
        )
        registrations = self._registrations_from_fields(
            address.country,
            address.state,
        )

        return ProfessionalProfile(
            full_name=full_name,
            preferred_name=self._optional_text(self._preferred_name),
            salutation=self._optional_text(self._salutation),
            registrations=registrations,
            email=self._optional_text(self._email),
            phone=self._optional_text(self._phone),
            address=address,
            practice_name=self._optional_text(self._practice_name),
            logo_reference=self._optional_string(self._logo.path if self._logo else None),
            signature_reference=self._optional_string(
                self._signature.path if self._signature else None
            ),
            regional_profile=self._combo_text(self._regional_profile, "BR"),
            document_language=self._combo_text(self._document_language, "pt-BR"),
        )

    def _registrations_from_fields(
        self,
        address_country: str | None,
        address_state: str | None,
    ) -> tuple[ProfessionalRegistration, ...]:
        existing_primary = self._primary_registration(self._loaded_profile)
        existing = self._loaded_profile.registrations if self._loaded_profile else ()
        others = [item for item in existing if item is not existing_primary]

        authority = self._optional_text(self._authority)
        number = self._optional_text(self._registration_number)
        region = self._optional_text(self._region_code) or self._optional_string(address_state)
        if authority is None and number is None:
            registrations = list(others)
        else:
            if authority is None or number is None:
                raise ValueError(
                    self._tr(
                        "professional.profile.registration_incomplete",
                        "Registration authority and number must be filled together.",
                    )
                )

            country = (
                address_country.upper()
                if address_country is not None and len(address_country.strip()) == 2
                else (existing_primary.country_code if existing_primary else "BR")
            )
            normalized_region = self._normalize_region(region, country)
            registration_id = (
                existing_primary.registration_id
                if existing_primary is not None
                else f"professional-registration-{uuid.uuid4().hex}"
            )
            registrations = [
                *others,
                ProfessionalRegistration(
                    registration_id=registration_id,
                    authority=authority,
                    country_code=country,
                    region_code=normalized_region,
                    registration_number=number,
                    is_primary=True,
                ),
            ]

        if registrations and not any(item.is_primary for item in registrations):
            first = registrations[0]
            registrations[0] = ProfessionalRegistration(
                registration_id=first.registration_id,
                authority=first.authority,
                country_code=first.country_code,
                region_code=first.region_code,
                registration_number=first.registration_number,
                is_primary=True,
            )
        return tuple(registrations)

    @staticmethod
    def _normalize_region(region: str | None, country: str) -> str | None:
        if region is None:
            return None
        value = region.strip().upper()
        if "-" not in value and len(value) == 2:
            return f"{country}-{value}"
        return value

    @staticmethod
    def _primary_registration(
        profile: ProfessionalProfile | None,
    ) -> ProfessionalRegistration | None:
        if profile is None or not profile.registrations:
            return None
        return next(
            (item for item in profile.registrations if item.is_primary),
            profile.registrations[0],
        )

    def _update_preview(self, *_args: object) -> None:
        if self._preview is None:
            return

        name = self._display_value(self._full_name)
        salutation = self._display_value(self._salutation, include_placeholder=False)
        if salutation and name:
            name = f"{salutation} {name}"
        registration = self._registration_preview()
        practice = self._display_value(self._practice_name)
        contact = " · ".join(
            value
            for value in (
                self._display_value(self._email, include_placeholder=False),
                self._display_value(self._phone, include_placeholder=False),
            )
            if value
        )
        address = self._address_preview()

        lines = [
            f"<b>{html.escape(name)}</b>",
            html.escape(registration),
            html.escape(practice),
        ]
        if contact:
            lines.append(html.escape(contact))
        if address:
            lines.append(html.escape(address))
        lines.append(
            "<hr>"
            + html.escape(
                self._tr(
                    "professional.profile.preview_signature",
                    "Each generated document will use the saved signature and profile data.",
                )
            )
        )
        self._preview.setText("<br>".join(lines))

    def _registration_preview(self) -> str:
        authority = self._optional_text(self._authority)
        number = self._optional_text(self._registration_number)
        region = self._optional_text(self._region_code)
        if authority is None and number is None:
            return self._tr(
                "professional.profile.no_registration",
                "No professional registration informed.",
            )
        parts = [part for part in (authority, number, region) if part]
        return " ".join(parts)

    def _address_preview(self) -> str:
        values = (
            self._optional_text(self._street),
            self._optional_text(self._number),
            self._optional_text(self._district),
            self._optional_text(self._city),
            self._optional_text(self._state),
            self._optional_text(self._country),
        )
        return ", ".join(value for value in values if value)

    def _on_signature_path_changed(self, path: str) -> None:
        preview = self._signature_preview
        if preview is None:
            return
        candidate = Path(path).expanduser() if path else None
        if candidate is None or not candidate.is_file():
            preview.clear()
        else:
            pixmap = QPixmap(str(candidate))
            if pixmap.isNull():
                preview.clear()
            else:
                preview.set_signature(pixmap)
        self._update_preview()

    # ----- Helpers ---------------------------------------------------

    def _tr(self, key: str, source: str, **params: object) -> str:
        context = self._context
        if context is None or context.translation_service is None:
            return source.format(**params) if params else source
        return context.translation_service.tr(key, source, **params)

    def _set_status(self, text: str, *, error: bool) -> None:
        if self._status_label is None:
            return
        self._status_label.setText(text)
        self._status_label.setProperty(
            "class",
            "feedback_error" if error else "feedback_success",
        )
        self._status_label.style().unpolish(self._status_label)
        self._status_label.style().polish(self._status_label)

    @staticmethod
    def _set_field(field: FormField | None, value: str | None) -> None:
        if field is not None:
            field.text = value or ""

    @staticmethod
    def _set_picker(picker: FilePicker | None, value: str | None) -> None:
        if picker is not None:
            picker.path = value or ""

    @staticmethod
    def _set_combo(combo: FormCombo | None, value: object) -> None:
        if combo is None:
            return
        if not combo.set_current_by_value(value):
            combo.add_item(str(value), value)
            combo.set_current_by_value(value)

    @staticmethod
    def _optional_text(field: FormField | None) -> str | None:
        if field is None:
            return None
        value = field.text.strip()
        return value or None

    @staticmethod
    def _optional_string(value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    def _required_text(
        self,
        field: FormField | None,
        field_name: str,
        label: str,
    ) -> str:
        value = self._optional_text(field)
        if value is None:
            raise ValueError(
                self._tr(
                    "professional.profile.required_field",
                    "{field} is required.",
                    field=label,
                )
            )
        return value

    @staticmethod
    def _combo_text(combo: FormCombo | None, default: str) -> str:
        if combo is None:
            return default
        value = combo.current_value
        return value if isinstance(value, str) and value else default

    def _display_value(
        self,
        field: FormField | None,
        *,
        include_placeholder: bool = True,
    ) -> str:
        value = self._optional_text(field)
        if value is not None:
            return value
        if include_placeholder:
            return self._tr("professional.profile.not_configured", "Not configured")
        return ""
