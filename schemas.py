"""
Database Schemas for Flamesblue

Each Pydantic model corresponds to a MongoDB collection. The collection
name is the lowercase of the class name (e.g., Order -> "order").
"""
from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime

# Brand-aligned domain models

class User(BaseModel):
    """Generic user account"""
    name: str = Field(..., description="Full name")
    phone: str = Field(..., description="Phone number for OTP login")
    email: Optional[str] = Field(None, description="Email address")
    address: Optional[str] = Field(None, description="Default address")
    role: Literal["customer", "driver", "admin"] = Field(
        "customer", description="Role in the system"
    )
    is_active: bool = Field(True, description="Whether user is active")

class Driver(BaseModel):
    """Driver profile (separate from the user account for extensibility)"""
    user_id: str = Field(..., description="Reference to User _id")
    vehicle_type: Optional[str] = Field(None, description="Bike, Car, Van")
    license_plate: Optional[str] = Field(None, description="Vehicle plate number")
    is_available: bool = Field(True, description="Driver availability")

class OrderItem(BaseModel):
    name: str = Field(..., description="Service item name (e.g., Shirt)")
    quantity: int = Field(..., ge=1)
    price: float = Field(..., ge=0)

class Order(BaseModel):
    customer_id: str = Field(..., description="Reference to User _id")
    driver_id: Optional[str] = Field(None, description="Reference to Driver _id")
    service_type: Literal["wash_fold", "dry_clean", "iron_only"]
    items: List[OrderItem] = Field(default_factory=list)
    pickup_address: str
    delivery_address: str
    scheduled_at: Optional[datetime] = Field(
        None, description="Scheduled pickup datetime (ISO8601)"
    )
    notes: Optional[str] = None
    status: Literal[
        "PENDING",
        "DRIVER_ASSIGNED",
        "PICKED_UP",
        "IN_WASH",
        "OUT_FOR_DELIVERY",
        "DELIVERED",
    ] = "PENDING"
    payment_method: Literal["cod", "card"] = "cod"
    total: float = Field(0, ge=0)

class Payment(BaseModel):
    order_id: str
    amount: float = Field(..., ge=0)
    method: Literal["cod", "card"]
    status: Literal["PENDING", "SUCCESS", "FAILED"] = "PENDING"
    transaction_id: Optional[str] = None
