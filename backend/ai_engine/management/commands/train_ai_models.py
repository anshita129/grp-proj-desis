from django.core.management.base import BaseCommand
from ai_engine.ml import get_training_dataframe, train_models


class Command(BaseCommand):
    help = "Train ML models for AI Trading Buddy"

    def handle(self, *args, **kwargs):
        try:
            df = get_training_dataframe()
            result = train_models(df)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Models trained successfully on {result['trained_users']} users with {result['n_clusters']} clusters."
                )
            )
        except ValueError as e:
            self.stdout.write(self.style.ERROR(str(e)))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Unexpected training error: {str(e)}"))