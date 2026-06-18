# vychron EKS Deployment Guide — AVI5211

## What was provisioned

vychron has set up the following for your EKS deployment:

- **ECR repositories** — one per detected service (see Terraform outputs)
- **ESO IRSA role** — External Secrets Operator reads AWS Secrets Manager without static keys
- **GitHub Actions ECR role** — CI/CD pushes Docker images using OIDC (no AWS secrets in GitHub)
- **GitOps repo** — `AVI5211/AVI5211-gitops-config` contains your Helm chart and ArgoCD manifests
- **ArgoCD** — watches the gitops repo and syncs your app to EKS automatically

## GitHub Repository Setup

After merging this PR, set the following in your repo's **Variables** (Settings → Secrets and variables → Actions → Variables):

| Variable | Value | Where to find it |
|---|---|---|
| *(pre-filled in workflow)* | *(already set in the workflow file)* | — |

> The IAM role ARN, ECR registry, and gitops repo are already embedded in the workflow file.
> No GitHub Variables needed — everything is pre-configured.

## IAM Trust Policy (verify after apply)

The GitHub Actions IAM role (`vychron-github-ecr-*`) has this trust policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {
      "Federated": "arn:aws:iam::<AWS_ACCOUNT_ID>:oidc-provider/token.actions.githubusercontent.com"
    },
    "Action": "sts:AssumeRoleWithWebIdentity",
    "Condition": {
      "StringLike": {
        "token.actions.githubusercontent.com:sub": "repo:AVI5211/AVI5211:ref:refs/heads/main"
      },
      "StringEquals": {
        "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
      }
    }
  }]
}
```

This trust policy only allows the `main` branch of **AVI5211/AVI5211** to assume the role.
PRs and other branches cannot assume this role.

## Deployment Flow (after merge)

```
git push → main
  ↓
GitHub Actions: vychron-build-push-eks
  ↓
OIDC → assume vychron-github-ecr role (no stored AWS secrets)
  ↓
ECR login → docker build → docker push (tag: sha-<commit>)
  ↓
Clone AVI5211/AVI5211-gitops-config
  ↓
python bin/update-image-tag.py --service <service> --tag sha-<commit>
  ↓
git push → gitops repo updated
  ↓
ArgoCD detects change → syncs → rolling update on EKS
  ↓
Pod running new image ✅
```

## Troubleshooting

**OIDC error: "Not authorized to perform sts:AssumeRoleWithWebIdentity"**
- Verify the IAM trust policy above has the correct repo (`AVI5211/AVI5211`)
- Check that the workflow is running from the `main` branch (PRs use a different ref)
- Run `terraform apply` again if the Terraform plan is not yet applied

**ECR push denied**
- Check that the ECR repositories exist: `aws ecr describe-repositories --region us-east-1`
- Verify the role has `ecr:PutImage` on the correct repository ARNs

**ArgoCD not syncing**
- Check ArgoCD UI: the app should show as `OutOfSync` then `Synced` within 3 minutes
- If stuck: `argocd app sync avi5211` manually
