from pydantic import BaseModel
from typing import Optional


class MortgageDetails(BaseModel):
    hasMortgage: bool
    paymentMethod: Optional[str] = None
    estPropertyValue: Optional[str] = None
    mortgageAmount: Optional[str] = None
    loanToValue1: Optional[str] = None
    furtherAdvance: Optional[str] = None
    mortgageType: Optional[str] = None
    productRateType: Optional[str] = None
    renewalDate: Optional[str] = None
    isLookingForMortgage: Optional[bool] = None
    newMortgageType: Optional[str] = None
    foundProperty: Optional[str] = None
    depositAmount: Optional[str] = None
    purchasePrice: Optional[str] = None
    loanToValue2: Optional[str] = None
    loanAmount: Optional[str] = None
    sourceOfDeposit: Optional[str] = None
    loanTerm: Optional[str] = None
    newPaymentMethod: Optional[str] = None
    reference1: Optional[str] = None
    reference2: Optional[str] = None

class ExistingMortgageDetails(BaseModel):
    id: str
    hasMortgage: bool
    paymentMethod: Optional[str] = None
    estPropertyValue: Optional[str] = None
    mortgageAmount: Optional[str] = None
    loanToValue1: Optional[str] = None
    furtherAdvance: Optional[str] = None
    mortgageType: Optional[str] = None
    productRateType: Optional[str] = None
    renewalDate: Optional[str] = None
    reference1: Optional[str] = None


class NewMortgageRequest(BaseModel):
    id: str
    isLookingForMortgage: bool
    newMortgageType: Optional[str] = None
    foundProperty: Optional[str] = None
    depositAmount: Optional[str] = None
    purchasePrice: Optional[str] = None
    loanToValue2: Optional[str] = None
    loanAmount: Optional[str] = None
    sourceOfDeposit: Optional[str] = None
    loanTerm: Optional[str] = None
    newPaymentMethod: Optional[str] = None
    reference2: Optional[str] = None