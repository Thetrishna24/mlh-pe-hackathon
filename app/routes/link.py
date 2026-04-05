# routes/links.py
from flask import Blueprint, jsonify, request, redirect
from playhouse.shortcuts import model_to_dict
from peewee import IntegrityError

from app.models.link import Link
from app.validators import validate_url, validate_short_code
from app import limiter

import logging
logger = logging.getLogger(__name__)

links_bp = Blueprint("links", __name__)

# Fields we're willing to serialize back to the client.
# Explicit allowlist — never serialize internal fields by accident.
_SAFE_FIELDS = {"id", "code", "url", "active"}


def _serialize(link: Link) -> dict:
    return {k: v for k, v in model_to_dict(link).items() if k in _SAFE_FIELDS}


@links_bp.route("/shorten", methods=["POST"])
@limiter.limit("10 per minute")
def shorten():
    """
    POST /shorten  {"url": "https://example.com"}
    → 201 {"id": 1, "code": "aB3xYz12", "url": "...", "active": true}

    Security: validates and sanitizes URL before any DB interaction.
    Returns 400 on bad input, 409 on duplicate, never a stack trace.
    """
    body = request.get_json(silent=True)

    # silent=True means Flask returns None instead of raising on bad JSON
    if not body or not isinstance(body, dict):
        return jsonify({"error": "Request body must be valid JSON"}), 400

    raw_url = body.get("url")
    ok, result = validate_url(raw_url)
    if not ok:
        return jsonify({"error": result}), 400
    # Check if we already have an active short link for this exact URL
    existing = Link.get_or_none(Link.url == result, Link.active == True)
    if existing:
        logger.info(f"Existing link found for URL: {result} -> code={existing.code}")
        return jsonify(_serialize(existing)), 200 # Note: 200 OK, not 201 Created
    # ---------------------------
    try:
        code = Link.generate_code()
        link = Link.create(url=result, code=code)
        logger.info(f"Link created: code={code} url={result}")
        return jsonify(_serialize(link)), 201
    except IntegrityError:
        # DB-level unique constraint fired (race condition safety net)
        logger.warning(f"Collision detected on code generation for URL: {result}")
        return jsonify({"error": "Could not generate a unique code, please retry"}), 409
    except RuntimeError as e:
        logger.error(f"System failure during link creation: {str(e)}")
        return jsonify({"error": str(e)}), 500


@links_bp.route("/r/<code>", methods=["GET"])
def redirect_link(code: str):
    """
    GET /r/<code>
    → 302 redirect on active link
    → 410 Gone if link was deactivated
    → 404 if code never existed

    Security: code is validated against allowlist before DB query
    to prevent path traversal or injection attempts via the URL path.
    """
    ok, result = validate_short_code(code)
    if not ok:
        return jsonify({"error": result}), 400

    try:
        link = Link.get(Link.code == result)
    except Link.DoesNotExist:
        logger.info(f"Redirect failed: code={result} not found")
        return jsonify({"error": "Short link not found"}), 404

    if not link.active:
        # 410 Gone: semantically distinct from 404. Client knows it existed.
        return jsonify({"error": "This link has been deactivated"}), 410
    logger.info(f"Redirecting: code={result} -> target={link.url}")
    return redirect(link.url, code=302)


@links_bp.route("/links/<int:link_id>", methods=["DELETE"])
def deactivate_link(link_id: int):
    """
    DELETE /links/<id>  — soft-deletes a link (sets active=False).
    Soft delete preserves audit trail and distinguishes 404 vs 410 on redirect.
    """
    try:
        link = Link.get_by_id(link_id)
    except Link.DoesNotExist:
        return jsonify({"error": "Link not found"}), 404

    link.active = False
    link.save()
    logger.info(f"Link deactivated: id={link_id} code={link.code}")
    return jsonify({"message": "Link deactivated", "code": link.code}), 200

@links_bp.route("/links", methods=["GET"])
def list_links():
    """
    GET /links
    → 200 [{"id": 1, "code": "...", "url": "...", "active": true}, ...]

    Retrieves all currently active links. 
    Observability: Logs the access for audit purposes.
    """
    try:
        # We only want to show active links to keep the list clean
        links = Link.select().where(Link.active == True)
        
        # Log that the directory was accessed
        logger.info(f"List links accessed: count={len(links)}")
        
        return jsonify([_serialize(l) for l in links]), 200
    except Exception as e:
        logger.error(f"Failed to retrieve links list: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500