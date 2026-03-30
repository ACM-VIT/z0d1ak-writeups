# Attachment Issues

| Field    | Value          |
| -------- | -------------- |
| Category | Cloud Security |
| Points   | 250            |
| Solves   | 14             |

## Description

It’s always the “final-backup” ones that get forgotten.
Especially when they’re left drifting.

```json
{
  "AccessKey": {
    "UserName": "ctf-user",
    "AccessKeyId": "REDACTED_AWS_ACCESS_KEY_ID",
    "Status": "Active",
    "SecretAccessKey": "REDACTED_AWS_SECRET_ACCESS_KEY",
    "CreateDate": "2026-03-26T06:06:06+00:00"
  }
}
```

Flag Format:
`hackzero{}`

## Writeup

## 1) Objective

Recover a `hackzero{...}` flag from an AWS challenge where leaked IAM access keys were provided and the clue emphasized a forgotten `final-backup` snapshot.

## 2) Initial Inputs

- IAM user: `ctf-user`

- Access key ID: `AKIAS32GSDY7NS3TLGJD`

- Secret key: provided during session (redacted here)

- Hint text: forgotten `final-backup`, “left drifting”

- Region signal from recon: `ap-south-1`

## 3) Environment Used

- Local analysis with Python (`boto3`) and AWS CLI

- AWS CloudShell for final exploit execution in a separate AWS account

- EC2 + EBS snapshot workflow

## 4) Recon & Permission Mapping

### 4.1 Credential validation

Used STS to confirm leaked key validity:

```bash

aws sts get-caller-identity

```

Observed identity:

- `arn:aws:iam::197179612734:user/ctf-user`

### 4.2 Service capability probing

Most actions were blocked with **explicit deny**.

Allowed:

- `ec2:DescribeSnapshots` (critical)

Denied (representative):

- `ec2:CreateVolume`

- `ec2:RunInstances`

- `ec2:RegisterImage`

- `ebs:ListSnapshotBlocks`

- IAM policy introspection (`iam:Get*`, `iam:List*`)

- STS privilege pivots (`AssumeRole`, `GetFederationToken`)

### 4.3 Snapshot discovery

Key command:

```bash

aws ec2 describe-snapshots --region ap-south-1 --owner-ids self

```

Primary finding:

- `snap-0c9fb7ec3494e18d0`

- Description: `final-backup`

- Volume size: `1 GiB`

- Encrypted: `false`

### 4.4 Public exposure check

Validated snapshot was publicly restorable:

```bash

aws ec2 describe-snapshots \

  --region ap-south-1 \

  --restorable-by-user-ids all \

  --snapshot-ids snap-0c9fb7ec3494e18d0

```

Result: snapshot returned under `all` scope.

## 5) Core Exploitation Logic

The leaked key was intentionally constrained to **discovery only**.

Direct extraction paths with that key were blocked by explicit deny.

Because the snapshot was public, data extraction required:

1. A different AWS principal/account (attacker-controlled account),

2. Create/attach volume from public snapshot,

3. Read filesystem/raw blocks to locate `hackzero{...}`.

## 6) CloudShell Execution Method (Working Path)

### 6.1 First attempts and issues

Issue A:

- Nested heredoc markers caused script truncation.

- Symptom: `Invalid endpoint: https://ec2..amazonaws.com`

- Root cause: empty `REGION`/vars due malformed script creation.

Fix:

- Use unique heredoc tags (`SCRIPT`, `USERDATA`, etc.).

Issue B:

- `aws ec2 wait instance-stopped` returned terminal failure in this CLI build when state was `pending`.

Fix:

- Replace waiter with manual polling loop using:

  - `describe-instances` for state

  - `get-console-output --latest` for logs/flag

Issue C:

- Console output initially missed user-data logs.

Fix:

- Force user-data output to serial console (`/dev/ttyS0`) using:

  - `exec > >(tee /dev/ttyS0 /var/log/user-data.log) 2>&1`

### 6.2 Final reliable method

High-level flow:

1. Resolve AL2023 AMI from SSM parameter.

2. Resolve default subnet in `ap-south-1a`.

3. Resolve default security group.

4. Launch `t3.micro` with extra EBS block device from snapshot:

   - `DeviceName=/dev/sdf`

   - EBS source: `snap-0c9fb7ec3494e18d0`

5. In user-data:

   - mount likely device paths read-only,

   - grep recursively for `hackzero{...}`,

   - if not found, run `strings` over block devices as fallback,

   - print `FINALFLAG:<value>` to serial console.

6. Poll console output until flag appears.

7. Terminate instance for cleanup.

## 7) Representative Commands (Condensed)

```bash

# Launch with snapshot-backed secondary volume

aws ec2 run-instances \

  --region ap-south-1 \

  --image-id "$AMI" \

  --instance-type t3.micro \

  --subnet-id "$SUBNET" \

  --security-group-ids "$SG" \

  --block-device-mappings "[{\"DeviceName\":\"/dev/sdf\",\"Ebs\":{\"SnapshotId\":\"snap-0c9fb7ec3494e18d0\",\"DeleteOnTermination\":true,\"VolumeType\":\"gp3\"}}]" \

  --user-data file://userdata3.sh



# Poll serial output

aws ec2 get-console-output \

  --region ap-south-1 \

  --instance-id "$IID" \

  --latest \

  --query Output \

  --output text

```

## 8) Cleanup Performed

Instances terminated after extraction attempts.

Verification:

```bash

aws ec2 describe-instances --region ap-south-1 --instance-ids <id> \

  --query 'Reservations[].Instances[].State.Name'

```

Observed state: `terminated`.

Recommended additional cleanup:

```bash

aws ec2 describe-volumes --region ap-south-1 \

  --filters Name=status,Values=available

```

Delete any orphaned `available` volumes not needed.

## 9) Methodology Summary

1. Validate leaked credentials.

2. Enumerate allowed actions quickly.

3. Identify high-value artifact (`final-backup` snapshot).

4. Confirm public snapshot exposure.

5. Recognize policy deny boundaries and pivot to second principal.

6. Automate extraction with user-data + serial output.

7. Troubleshoot provisioning/logging/wait semantics.

8. Extract flag and clean up resources.

## 10) Security Lessons

- Publicly restorable EBS snapshots are highly sensitive.

- Explicit-deny least privilege worked for discovery account but did not mitigate data exposure from public snapshot configuration.

- Continuous checks should include:

  - snapshot sharing audits (`all`),

  - auto-remediation for accidental public exposure,

  - CloudTrail alerts on snapshot sharing changes.

## 11) Session Notes

- Challenge behavior strongly indicates design pattern:

  - leaked key for reconnaissance only,

  - real exfiltration path through public snapshot misuse.

- This is why direct use of `ctf-user` never succeeded for mount/read operations despite correct credentials.

Instead of babysitting the instance manually, I looped `aws ec2 get-console-output --latest --instance-id $IID --region ap-south-1` until the user-data script wrote out the flag. When `/mnt/flagvol/home/ec2-user/flag.txt` finally yielded content, the console spat back:

### Flag

```
hackzero{8bc7ff831fdb83fdd07432cf89b6c059}
```

### Executive Summary

### Vulnerability Analysis

### Exploit Strategy

### Implementation

### Execution & Results
