#!/bin/sh
set -eu

mc alias set local http://files:9000 "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD" >/dev/null

for bucket in local-static local-media builds; do
    mc mb --ignore-existing "local/$bucket" >/dev/null
done

mc anonymous set download local/local-static >/dev/null
mc anonymous set download local/builds >/dev/null

storage_is_root=0
if ! mc admin user info local "$MINIO_STORAGE_ACCESS_KEY" >/dev/null 2>&1; then
    if ! user_error=$(mc admin user add local "$MINIO_STORAGE_ACCESS_KEY" "$MINIO_STORAGE_SECRET_KEY" 2>&1); then
        case "$user_error" in
            *"Credential is not allowed to be same as admin access key"*)
                storage_is_root=1
                ;;
            *)
                printf '%s\n' "$user_error" >&2
                exit 1
                ;;
        esac
    fi
fi

cat > /tmp/rmc-backend-storage-policy.json <<'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:GetBucketLocation", "s3:ListBucket", "s3:ListBucketMultipartUploads"],
      "Resource": ["arn:aws:s3:::local-static", "arn:aws:s3:::local-media", "arn:aws:s3:::builds"]
    },
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:PutObject", "s3:DeleteObject", "s3:AbortMultipartUpload", "s3:ListMultipartUploadParts"],
      "Resource": ["arn:aws:s3:::local-static/*", "arn:aws:s3:::local-media/*", "arn:aws:s3:::builds/*"]
    }
  ]
}
EOF

mc admin policy create local rmc-backend-storage /tmp/rmc-backend-storage-policy.json \
    >/dev/null 2>&1 || true
if [ "$storage_is_root" -eq 0 ]; then
    mc admin policy attach local rmc-backend-storage --user "$MINIO_STORAGE_ACCESS_KEY" \
        >/dev/null
fi

echo "MinIO storage initialized"
