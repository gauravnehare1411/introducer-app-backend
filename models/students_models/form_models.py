from pydantic import BaseModel
from typing import List, Optional

class HighestQualification(BaseModel):
    type: str
    school: str
    board: str
    year: str
    percentage: str

class PreviousQualification(BaseModel):
    type: Optional[str] = None
    school: Optional[str] = None
    board: Optional[str] = None
    year: Optional[str] = None
    percentage: Optional[str] = None

class Educational(BaseModel):
    highestQualification: HighestQualification  # required
    previousQualifications: Optional[List[PreviousQualification]] = []

class StudyPreferences(BaseModel):
    preferredCountry: Optional[str] = None
    preferredCourse: Optional[str] = None
    preferredIntakeMonth: Optional[str] = None
    preferredIntakeYear: Optional[str] = None
    degreeLevel: Optional[str] = None
    preferredUniversities: Optional[str] = None

class Scores(BaseModel):
    ielts: Optional[str] = None
    toefl: Optional[str] = None
    pte: Optional[str] = None

class Certifications(BaseModel):
    hasCertifications: bool
    scores: Optional[Scores] = None

class Experience(BaseModel):
    jobTitle: Optional[str] = None
    isRelated: Optional[str] = None
    companyName: Optional[str] = None
    years: Optional[str] = None

class WorkExperience(BaseModel):
    hasExperience: bool
    experience: Optional[Experience] = None

class FinancialInformation(BaseModel):
    estimatedBudget: Optional[str] = None
    sourceOfFunding: Optional[str] = None

class ApplicationForm(BaseModel):
    educational: Educational  # required
    studyPreferences: Optional[StudyPreferences] = None
    certifications: Optional[Certifications] = None
    workExperience: Optional[WorkExperience] = None
    financialInformation: Optional[FinancialInformation] = None

class StatusUpdate(BaseModel):
    status: str