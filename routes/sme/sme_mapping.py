from fastapi import APIRouter, Query
from datetime import datetime
from bson import ObjectId
from bson.errors import InvalidId
import traceback
from config.database import sme_mapping_collection
from utils.response import success, failed
from utils.email_sender import send_email

router = APIRouter(prefix="/sme", tags=["sme"])

NOTIFY_EMAIL = "guggarividyashri1@gmail.com"
@router.patch("/update-level/{sme_mapping_id}")
def update_level(sme_mapping_id: str,level: str = Query(...)):
    try:
        allowed_levels = ["L1", "L2", "L3"]
        if level not in allowed_levels:
            return failed("Invalid level", 400)

        try:
            obj_id = ObjectId(sme_mapping_id)
        except InvalidId:
            return failed("Invalid sme_mapping_id", 400)

        existing = sme_mapping_collection.find_one({"_id": obj_id})
        if not existing:
            return failed("SME mapping not found", 404)

        old_level = existing.get("level")

        if old_level == level:
            return failed("Same level provided, no update needed")

        sme_mapping_collection.update_one(
            {"_id": obj_id},
            {
                "$set": {
                    "level": level,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #f4f6f8; padding: 20px;">
            <div style="max-width: 600px; margin: auto; background: #ffffff; border-radius: 10px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                
                <h2 style="color: #2c3e50; text-align: center;">SME Mapping Updated</h2>
                
                <p style="font-size: 16px; color: #333;">
                    The SME mapping level has been successfully updated.
                </p>

                <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
                    <tr>
                        <td style="padding: 10px; font-weight: bold;">Benchmark</td>
                        <td style="padding: 10px;">{existing.get('benchmark_name')}</td>
                    </tr>
                    <tr style="background-color: #f9f9f9;">
                        <td style="padding: 10px; font-weight: bold;">Mapping ID</td>
                        <td style="padding: 10px;">{sme_mapping_id}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; font-weight: bold;">Old Level</td>
                        <td style="padding: 10px; color: red;">{old_level}</td>
                    </tr>
                    <tr style="background-color: #f9f9f9;">
                        <td style="padding: 10px; font-weight: bold;">New Level</td>
                        <td style="padding: 10px; color: green;">{level}</td>
                    </tr>
                </table>

                <p style="margin-top: 20px; font-size: 14px; color: #777;">
                    Status: Update successful and recorded in the system.
                </p>

                <hr style="margin: 20px 0;">
                <p style="text-align: center; font-size: 12px; color: #aaa;">
                    This is an automated notification. Please do not reply.
                </p>

            </div>
        </body>
        </html>
        """

        send_email(
            NOTIFY_EMAIL,
            f"SME Mapping Updated to {level}",
            body
        )

        return success(
            "Level updated successfully",
            {
                "sme_mapping_id": sme_mapping_id,
                "old_level": old_level,
                "new_level": level,
                "email_sent": True
            }
        )

    except Exception as e:
        print(traceback.format_exc())
        return failed(str(e), 500)