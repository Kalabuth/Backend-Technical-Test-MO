from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from apps.common.models.base_model import BaseModel
from apps.users.managers.user_manager import UserManager


class User(BaseModel, AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True, null=False, blank=False)
    first_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100, null=True, blank=True)
    is_staff = models.BooleanField(default=False)
    change_password = models.BooleanField(default=True)

    USERNAME_FIELD = "email"
    objects = UserManager()

    SAVE_DELETED_DATA_TO_FILE = True

    @property
    def full_name(self):
        return (
            f"{self.first_name} {self.last_name}"
            if self.first_name and self.last_name
            else self.email
        )

    def __str__(self):
        return f"{self.email}"
